"""制课：一个 PDF 进来，一套可练的卷出去。

制作台原来把流水线的八个阶段逐个摆在人面前，每一步都要人按一下。那对"这一
页到底怎么处置"是必要的，对"这 20 套卷先跑起来"是负担。所以这里把能自动的
部分连成一条任务：

    登记 → 探测 → 渲染 → 读文本 → 读解答欄号
        → 校对·复读异常页 → 页面合同与机器校验
        → 组装与预检 → 校对·复核整卷 → 发布 → 真题详解草稿

这条任务**没有放松任何闸门**。它走的是和手签卷一样的
``candidate → approve → publish``，签名用的是 ``MACHINE_REVIEWER``，所以卷子
一路带着 ``reviewGrade: MACHINE_ATTESTED`` 到学习者屏幕上 —— 页面上机器读了
什么、人还没看什么，学习者看得到。想要人工复核的卷，勾上"停在待复核"，
任务就在组装预检之后停下，等人去复核编辑器逐页签。

每一步都可断点续跑：产物已经在了就跳过，除非明确要求重跑。取消在步与步之间
和长步骤内部都有检查点，停下来时已经做完的产物都留着。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .errors import ContractError
from .util import load_json, sha256_file, utc_now, write_json

# 步骤表就是界面上那条进度条。key 会进任务进度 JSON，label 直接显示。
STEPS: tuple[tuple[str, str], ...] = (
    ("REGISTER", "登记与导入"),
    ("PROBE", "探测页面"),
    ("RENDER", "渲染原页"),
    ("OCR_TEXT", "读文本"),
    ("OCR_SLOTS", "读解答欄号"),
    ("PROOFREAD_PAGES", "校对 · 复读异常页"),
    ("ATTEST", "页面合同与机器校验"),
    ("ASSEMBLE", "组装与预检"),
    ("PROOFREAD_PAPER", "校对 · 复核整卷"),
    ("PUBLISH", "发布到题库"),
    ("EXPLAIN", "真题详解草稿"),
)

LOG_LIMIT = 240
ROLES = ("QUESTION_BOOKLET", "ANSWER_KEY")


class Run:
    """一次制课的状态：步骤进度 + 日志。两者都写进任务进度，供页面轮询。"""

    def __init__(self, report: Callable[[dict[str, Any]], None]) -> None:
        self._report = report
        self.steps = [{"key": key, "label": label, "status": "pending", "detail": ""}
                      for key, label in STEPS]
        self.log: list[str] = []
        self.facts: dict[str, Any] = {}
        self.current = 0

    def _snapshot(self) -> dict[str, Any]:
        done = sum(1 for s in self.steps if s["status"] in {"done", "skipped"})
        return {
            "stage": self.steps[self.current]["key"] if self.current < len(self.steps) else "DONE",
            "percent": round(100 * done / len(self.steps)),
            "steps": self.steps,
            "log": self.log[-LOG_LIMIT:],
            **self.facts,
        }

    def push(self) -> None:
        self._report(self._snapshot())

    def say(self, line: str) -> None:
        self.log.append(line)
        self.push()

    def fact(self, **values: Any) -> None:
        self.facts.update(values)
        self.push()

    def begin(self, key: str) -> None:
        self.current = next(i for i, s in enumerate(self.steps) if s["key"] == key)
        self.steps[self.current]["status"] = "running"
        self.steps[self.current]["startedAt"] = utc_now()
        self.say(f"▶ {self.steps[self.current]['label']}")

    def end(self, key: str, detail: str = "", status: str = "done") -> None:
        step = next(s for s in self.steps if s["key"] == key)
        step["status"] = status
        step["detail"] = detail
        step["endedAt"] = utc_now()
        mark = {"done": "✓", "skipped": "–", "failed": "✗"}.get(status, "·")
        self.say(f"{mark} {step['label']}{'：' + detail if detail else ''}")

    def skip(self, key: str, detail: str) -> None:
        self.end(key, detail, status="skipped")


def _profile(root: Path, family: str, name: str | None, *, required: bool) -> dict[str, Any] | None:
    from .model_profiles import resolve
    if not name:
        if required:
            raise ContractError(f"Select a {family} profile for this run")
        return None
    return resolve(root, family, name)


def _ocr_url(profile: dict[str, Any]) -> str:
    return profile["baseUrl"].rstrip("/") + "/chat/completions"


# ── ① 登记与导入 ──────────────────────────────────────────────────────────

def register(run: Run, root: Path, database: Any, params: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    """把上传的 PDF 变成一套登记过的来源。已经登记过就原样复用。"""
    from .inventory import get_inventory_item, upsert_inventory_item
    from .paper_naming import expected_forms, inventory_id, syllabus_version, work_dir_name
    from .source import create_source_manifest, validate_source_manifest
    from .uploads import resolve as resolve_upload

    session = str(params["session"])
    subject = str(params["subject"])
    course = params.get("course") or None
    language = str(params.get("language") or "ja")
    year = int(session.split("-")[0])

    booklet = resolve_upload(root, params["questionBooklet"])
    answer = resolve_upload(root, params["answerKey"]) if params.get("answerKey") else None
    forms = expected_forms(subject, course, language)
    if not forms:
        raise ContractError(f"Cannot derive exam forms for {subject}/{course}")

    work = root / "work" / work_dir_name(session, subject, course)
    manifest_path = work / "source-manifest.json"
    iid = inventory_id(session, subject, course, language)

    inventory_path = root / "content/content-inventory.json"
    if not get_inventory_item(iid, inventory_path):
        upsert_inventory_item({
            "inventoryId": iid, "session": session, "subject": subject, "language": language,
            "syllabusId": syllabus_version(subject, year),
            "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
            "rightsStatus": "PRIVATE_STUDY",
            "pipelineStatus": "RECEIVED",
            "expectedForms": forms,
            "blockingIssues": [] if answer else ["MISSING_ANSWER"],
            "notes": f"制课台上传：{booklet.name}" + (f" + {answer.name}" if answer else ""),
        }, inventory_path=inventory_path)
        run.say(f"  · 已登记清单条目 {iid}")
    else:
        run.say(f"  · 清单条目 {iid} 已存在，沿用")

    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        validate_source_manifest(manifest, manifest_path, verify_files=True)
        # 工作目录的名字只由场次和科目决定，所以"目录已存在"完全不表示"上传的是
        # 同一份文件"。原来到这里就整份沿用旧清单：用户拖进来一份新扫描件，流水线
        # 读的是上一次那份，而且什么都不说。来源身份必须按内容比。
        recorded = {f["role"]: f["sha256"] for f in manifest["files"]}
        incoming = {"QUESTION_BOOKLET": sha256_file(booklet)}
        if answer is not None:
            incoming["ANSWER_KEY"] = sha256_file(answer)

        if recorded.get("QUESTION_BOOKLET") != incoming["QUESTION_BOOKLET"]:
            # sourceId 由题册内容派生，所以换了题册就是另一个来源版本 —— 它需要
            # 自己的工作目录，以及把旧版的逻辑题号、人工锁、音轨接过去的沿袭映射。
            # 那套机制还没有（规范 W05）。在它到位之前，宁可明确拒绝：拿旧文件
            # 冒充新上传，比报错难发现得多。
            raise ContractError(
                f"工作目录 {work.name} 已登记的题册与本次上传的不是同一份文件"
                f"（已登记 {recorded.get('QUESTION_BOOKLET', '无')[:12]}…，"
                f"本次 {incoming['QUESTION_BOOKLET'][:12]}…）。"
                "同一场次科目的新扫描件是新的来源版本，需要新的 sourceId 和来源沿袭"
                "映射，目前尚未实现，因此不会沿用旧文件。"
                "请另用工作目录，或先移走旧目录再重新上传。")

        if "ANSWER_KEY" in incoming and "ANSWER_KEY" in recorded \
                and recorded["ANSWER_KEY"] != incoming["ANSWER_KEY"]:
            raise ContractError(
                f"工作目录 {work.name} 已登记的答案册与本次上传的不是同一份文件"
                f"（已登记 {recorded['ANSWER_KEY'][:12]}…，本次 {incoming['ANSWER_KEY'][:12]}…）。"
                "换正解表会改变全部题答对应和据此签发的证明，不能就地覆盖。"
                "请另用工作目录，或先移走旧目录再重新上传。")

        if "ANSWER_KEY" in incoming and "ANSWER_KEY" not in recorded:
            # 后补答案册：题册没变，sourceId 由题册内容派生，所以它不变。清单补上
            # 这一份文件，题答对应和下游证明会按新的输入重新建立。
            manifest = create_source_manifest(
                session=session, subject=subject, language=language,
                syllabus_version=syllabus_version(subject, year) or "basic-2015",
                question_booklet=booklet, answer_key=answer,
                rights_status="PRIVATE_STUDY",
                rights_note=f"EJU {session} {subject} personal study copy",
                output_path=manifest_path)
            run.say(f"  · 来源 {manifest['sourceId']} 补入答案册，题答对应将重新建立")
        else:
            roles = {f["role"] for f in manifest["files"]}
            run.say(f"  · 来源 {manifest['sourceId']} 已存在，沿用（{'、'.join(sorted(roles))}）")
    else:
        work.mkdir(parents=True, exist_ok=True)
        manifest = create_source_manifest(
            session=session, subject=subject, language=language,
            syllabus_version=syllabus_version(subject, year) or "basic-2015",
            question_booklet=booklet, answer_key=answer,
            rights_status="PRIVATE_STUDY",
            rights_note=f"EJU {session} {subject} personal study copy",
            output_path=manifest_path)
        run.say(f"  · 已建立来源 {manifest['sourceId']}")

    # inventoryId 与 expectedForms 不在 create_source_manifest 的参数里，
    # 但组卷闸门要靠它们判断"这套卷该有几科"。
    if manifest.get("inventoryId") != iid or manifest.get("expectedForms") != forms:
        manifest["inventoryId"] = iid
        manifest["expectedForms"] = forms
        write_json(manifest_path, manifest)
    run.fact(sourceId=manifest["sourceId"], inventoryId=iid,
             workDir=str(work.relative_to(root)),
             expectedForms=forms,
             hasAnswerKey=bool(answer))
    return manifest_path, manifest


# ── ② 探测 / ③ 渲染 ──────────────────────────────────────────────────────

def probe(run: Run, manifest_path: Path, force: bool) -> str:
    from .pdf_pipeline import probe_manifest
    target = manifest_path.parent / "probe.json"
    if target.is_file() and not force:
        data = load_json(target)
        pages = sum(int(f.get("pageCount") or 0) for f in data.get("files") or [])
        return f"已有探测结果，共 {pages} 页"
    data = probe_manifest(manifest_path, target)
    pages = sum(int(f.get("pageCount") or 0) for f in data.get("files") or [])
    blanks = sum(1 for f in data.get("files") or [] for p in f.get("pages") or []
                 if p.get("likelyBlank"))
    return f"{pages} 页，其中 {blanks} 页无墨"


def render(run: Run, manifest_path: Path, manifest: dict[str, Any], force: bool,
           cancelled: Callable[[], bool], progress: Callable[[str, int, int], None]) -> str:
    from .pdf_pipeline import render_manifest
    root = manifest_path.parent / "renders"
    present = {f["role"] for f in manifest["files"]}
    counts: list[str] = []
    for role in ROLES:
        if role not in present:
            run.say(f"  · 没有{'题册' if role == 'QUESTION_BOOKLET' else '答案册'}，跳过")
            continue
        index = root / f"render-index-{role.lower()}.json"
        if index.is_file() and not force:
            counts.append(f"{role} 已有 {len(load_json(index).get('pages') or [])} 页")
            continue
        result = render_manifest(
            manifest_path, role=role, output_dir=root,
            cancelled=cancelled,
            on_progress=lambda done, total, role=role: progress(role, done, total))
        counts.append(f"{role} {len(result['pages'])} 页")
    return "；".join(counts) or "无可渲染文件"


# ── ④ 本地 OCR 两步 ──────────────────────────────────────────────────────

def ocr_text(run: Run, work: Path, manifest: dict[str, Any], profile: dict[str, Any],
             force: bool, cancelled, progress) -> str:
    from .ocr.local_vision import ocr_source_pages
    roles = [r.lower() for r in ROLES if r in {f["role"] for f in manifest["files"]}]
    result = ocr_source_pages(work, roles=roles, url=_ocr_url(profile),
                              model=profile["model"], force=force,
                              cancelled=cancelled, on_progress=progress)
    return (f"读了 {result['completed']}/{result['pages']} 页"
            + (f"，{result['failed']} 页失败" if result["failed"] else "")
            + ("（全部已有读法，跳过）" if result["pages"] == 0 else ""))


def ocr_slots(run: Run, work: Path, profile: dict[str, Any], force: bool,
              cancelled, progress) -> str:
    from .ocr.local_vision import ocr_source_slots
    result = ocr_source_slots(work, url=_ocr_url(profile), model=profile["model"],
                              force=force, cancelled=cancelled, on_progress=progress)
    return (f"读了 {result['completed']}/{result['pages']} 页解答欄号"
            + (f"，{result['failed']} 页失败" if result["failed"] else "")
            + ("（全部已有读法，跳过）" if result["pages"] == 0 else ""))


# ── 校对① 复读异常页 ─────────────────────────────────────────────────────

def proofread_pages(run: Run, work: Path, profile: dict[str, Any],
                    cancelled, progress) -> tuple[str, dict[str, Any]]:
    from .proofread import reread_pages, suspicious_pages
    pages = suspicious_pages(work)
    if not pages:
        return "首轮读法没有可检出的异常页", {"pagesChecked": 0, "replaced": [], "kept": []}
    run.say(f"  · 挑出 {len(pages)} 页有出错痕迹，交给 {profile['model']} 重读")
    report = reread_pages(work, pages, profile, cancelled=cancelled,
                          on_progress=progress, on_log=run.say)
    write_json(work / "proofread-pages.json", report)
    return (f"复读 {report['pagesChecked']} 页，{len(report['replaced'])} 页顶替首轮"
            + (f"，{report['failed']} 页失败" if report["failed"] else "")), report


# ── 校对② + 机器校验 ─────────────────────────────────────────────────────

def attest(run: Run, workspace: Any, work: Path, manifest: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    from .attest import clear_source
    stats = clear_source(workspace, work, manifest)
    # 答案与选项的交叉反验就在 clear_source 里。它的结论要说出来，
    # 否则"机器校验过了"是一句没有内容的话。
    join = stats.get("join_report") or {}
    if isinstance(join, dict) and join:
        agreed = join.get("agreement") or join.get("agreed")
        if agreed is not None:
            run.say(f"  · 正解表答案与题册选项一致率：{agreed}")
    if stats.get("provisional_accepted"):
        run.say(f"  · 按小节顺序补齐并通过反验的欄号：{len(stats['provisional_accepted'])} 个")
    if stats.get("slots_filled"):
        run.say(f"  · 补齐解答欄 {stats['slots_filled']} 处")
    if stats.get("contested"):
        run.say(f"  · {stats['contested']} 个解答欄被多题争用，相关题目一律不收录")
    for problem in (stats.get("errors") or [])[:6]:
        run.say(f"  ✗ {problem}")
    cleared = stats["cleared"]
    return (f"题册 {stats['booklet_attested']}/{stats['booklet_pages']} 页、"
            f"答案 {stats['answer_attested']}/{stats['answer_pages']} 页通过机器校验"), stats


# ── 组装 / 校对③ / 发布 ──────────────────────────────────────────────────

class NothingToAssemble(Exception):
    """机器校验一页都没通过，这一套卷这次装不出来。

    这不是流水线坏了，是这份原卷的读法还不够 —— 命令行那条路遇到同样情况打的是
    「无可发布页，跳过」。所以它不当异常往上抛：任务照常收尾，把差在哪写清楚，
    人拿着这份报告去复核编辑器补。
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def assemble(run: Run, workspace: Any, manifest: dict[str, Any],
             stats: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    from .attest import baseline_and_candidate
    cleared = stats["cleared"]
    if not cleared["QUESTION_BOOKLET"]:
        raise NothingToAssemble(
            f"题册 {stats['booklet_pages']} 页里没有一页通过机器校验，这一版装不出来。"
            "常见原因是答案表没读通（答案对不上题册印的选项），或解答欄号没读到。")
    if not cleared["ANSWER_KEY"]:
        raise NothingToAssemble(
            f"答案册 {stats['answer_pages']} 页里没有一页带本卷的答案条目，无法定稿答案。"
            "确认上传的答案册是这一回次的，或先把答案页读通。")
    staged = baseline_and_candidate(workspace, manifest, cleared,
                                    form_refs=stats.get("form_refs"))
    paper = staged["candidate"]["paper"]
    return (f"{paper.get('questionCount')} 题 · {paper.get('completeness')} · "
            f"{len(staged['candidate']['pageRevisionIds'])} 页在发布范围内"), staged


def proofread_paper(run: Run, work: Path, paper: dict[str, Any], profile: dict[str, Any],
                    cancelled, progress) -> tuple[str, dict[str, Any]]:
    from .proofread import review_paper
    report = review_paper(paper, profile, cancelled=cancelled, on_progress=progress,
                          on_log=run.say)
    write_json(work / "proofread-report.json", report)
    coverage = report.get("coverage") or {}
    # 覆盖不全时不能说"没有疑点"：一批都没查成和查过都没问题，findings 同样是空的，
    # 结论却正好相反。
    if coverage.get("result") not in {"PASS", "NOT_APPLICABLE"}:
        run.say(f"  ! {coverage.get('explanation') or '复核覆盖不完整'}")
    for kind, count in sorted(report["byKind"].items()):
        run.say(f"  · {kind}：{count} 题")
    if not report["findings"]:
        if coverage.get("result") == "PASS":
            return f"读了 {report['questionsReviewed']} 题，覆盖完整，没有报出转写疑点", report
        return (f"读了 {report['questionsReviewed']} 题，"
                f"{coverage.get('explanation') or '覆盖不完整'}"), report
    return (f"读了 {report['questionsReviewed']} 题，报出 {len(report['findings'])} 处疑点"), report


def publish(run: Run, workspace: Any, manifest: dict[str, Any], staged: dict[str, Any],
            channel: str) -> tuple[str, dict[str, Any]]:
    from .attest import approve_and_publish
    result = approve_and_publish(workspace, manifest["sourceId"], staged["candidate"],
                                 staged["contentDigest"], channel=channel,
                                 scope=staged.get("scope", "REVIEWED_PARTIAL"))
    return (f"{result['paperId']} 第 {result['version']} 版 · "
            f"{result['questions']} 题 · {result['grade']}"), result


def explain(run: Run, database: Any, paper: dict[str, Any], paper_version_id: str,
            profile: dict[str, Any], findings: list[dict[str, Any]], limit: int,
            cancelled, progress) -> str:
    from .explain import generate
    suspect = {f["questionId"] for f in findings or []}
    if suspect:
        run.say(f"  · {len(suspect)} 题转写有疑点，先不写详解")
    report = generate(paper, profile, database, paper_version_id,
                      skip_question_ids=suspect, limit=limit,
                      cancelled=cancelled, on_progress=progress, on_log=run.say)
    return (f"写了 {len(report['written'])}/{report['candidates']} 题详解草稿"
            + (f"，{len(report['errors'])} 题失败" if report["errors"] else "")
            + "；草稿要人改成 REVIEWED 才会显示给学习者")


# ── 全流程 ───────────────────────────────────────────────────────────────

def run_pipeline(*, root: Path, database: Any, workspace: Any, params: dict[str, Any],
                 report: Callable[[dict[str, Any]], None],
                 cancelled: Callable[[], bool],
                 checkpoint: Callable[[], None]) -> dict[str, Any]:
    """从上传的 PDF 一路做到可练的卷。返回写进任务进度的收尾结果。"""
    run = Run(report)
    force = bool(params.get("force"))
    stop_at_draft = bool(params.get("stopAtDraft"))
    channel = str(params.get("channel") or "PRIVATE")

    ocr_profile = _profile(root, "vision", params.get("ocrProfile"), required=True)
    review_profile = _profile(root, "vision", params.get("proofreadProfile"), required=False)
    text_profile = _profile(root, "text", params.get("textProfile"), required=False)
    explain_profile = _profile(root, "text", params.get("explainProfile"), required=False)
    run.fact(models={
        "ocr": ocr_profile["model"],
        "proofreadPages": review_profile["model"] if review_profile else None,
        "proofreadPaper": text_profile["model"] if text_profile else None,
        "explain": explain_profile["model"] if explain_profile else None,
    }, stopAtDraft=stop_at_draft)

    def pages_progress(stage: str):
        def emit(done: int, total: int, failed: int = 0) -> None:
            run.steps[run.current]["detail"] = (
                f"{done}/{total}" + (f"（{failed} 失败）" if failed else ""))
            run.facts["pagesCompleted"] = done
            run.facts["pagesTotal"] = total
            run.facts["pagesFailed"] = failed
            run.push()
        return emit

    run.begin("REGISTER")
    manifest_path, manifest = register(run, root, database, params)
    work = manifest_path.parent
    run.end("REGISTER", f"来源 {manifest['sourceId']}")
    checkpoint()

    run.begin("PROBE")
    run.end("PROBE", probe(run, manifest_path, force))
    checkpoint()

    run.begin("RENDER")
    run.end("RENDER", render(run, manifest_path, manifest, force, cancelled,
                             lambda role, done, total: pages_progress("RENDER")(done, total)))
    checkpoint()

    run.begin("OCR_TEXT")
    run.end("OCR_TEXT", ocr_text(run, work, manifest, ocr_profile, force,
                                 cancelled, pages_progress("OCR_TEXT")))
    checkpoint()

    run.begin("OCR_SLOTS")
    run.end("OCR_SLOTS", ocr_slots(run, work, ocr_profile, force,
                                   cancelled, pages_progress("OCR_SLOTS")))
    checkpoint()

    if review_profile and params.get("proofreadPages", True):
        run.begin("PROOFREAD_PAGES")
        detail, _ = proofread_pages(run, work, review_profile, cancelled,
                                    pages_progress("PROOFREAD_PAGES"))
        run.end("PROOFREAD_PAGES", detail)
    else:
        run.skip("PROOFREAD_PAGES", "本次未选复核模型")
    checkpoint()

    run.begin("ATTEST")
    detail, stats = attest(run, workspace, work, manifest)
    run.end("ATTEST", detail)
    checkpoint()

    run.begin("ASSEMBLE")
    try:
        detail, staged = assemble(run, workspace, manifest, stats)
    except NothingToAssemble as exc:
        run.end("ASSEMBLE", exc.reason, status="failed")
        for key in ("PROOFREAD_PAPER", "PUBLISH", "EXPLAIN"):
            run.skip(key, "没有可组装的内容")
        return {
            "jobStatus": "PARTIAL_FAILED",
            "steps": run.steps, "log": run.log[-LOG_LIMIT:],
            "sourceId": manifest["sourceId"], "workDir": str(work.relative_to(root)),
            "blocked": exc.reason,
            "attest": {k: stats.get(k) for k in
                       ("booklet_pages", "booklet_attested", "answer_pages",
                        "answer_attested", "unchanged", "contested", "slots_filled")},
            "attestErrors": (stats.get("errors") or [])[:20],
            "reviewRequired": True,
            **run.facts,
        }
    run.end("ASSEMBLE", detail)
    paper = staged["candidate"]["paper"]
    checkpoint()

    findings: list[dict[str, Any]] = []
    quality: dict[str, Any] = {}
    if text_profile and params.get("proofreadPaper", True):
        from .quality import Coverage, classify, resolve_quarantine, summarise
        from .attest import quarantine_questions, baseline_and_candidate

        run.begin("PROOFREAD_PAPER")
        detail, paper_report = proofread_paper(run, work, paper, text_profile, cancelled,
                                               lambda done, total: pages_progress(
                                                   "PROOFREAD_PAPER")(done, total))
        findings = paper_report["findings"]
        raw_coverage = paper_report.get("coverage") or {}
        coverage = Coverage(planned=raw_coverage.get("planned", 0),
                            completed=raw_coverage.get("completed", 0),
                            failed=raw_coverage.get("failed", 0),
                            cancelled=bool(raw_coverage.get("cancelled")))
        # 模型报的是信号，不是定级。服务端能独立复核的自己算一遍，算不了的停在
        # SUSPECT —— 未证实的高风险疑点按 §6.3 隔离，而不是当作没问题放行。
        structured = classify(findings, paper, source_id=manifest["sourceId"],
                              generation=1,
                              input_digest=staged["contentDigest"])
        quality = summarise(structured, coverage)
        quality["findings"] = structured
        write_json(work / "quality-findings.json", quality)

        # 隔离的单位是依赖组：材料级的问题扩散到依赖它的全部题目，
        # 一道题自己的问题则只影响它自己（规范 §6.5）。
        drop, reasons = resolve_quarantine(structured, paper)
        if drop:
            quality["quarantinedQuestions"] = sorted(drop)
            run.say(f"  · {len(drop)} 题未能确认，隔离后继续发布其余内容")
            moved = quarantine_questions(workspace, manifest, stats["cleared"], reasons)
            quality["quarantine"] = moved
            if moved["humanHeld"]:
                run.say(f"  · {len(moved['humanHeld'])} 页归人工持有，隔离只作记录，未改写")
            # 范围变了就必须重新组装：发布的内容要和实际通过的处置一致。
            staged = baseline_and_candidate(workspace, manifest, stats["cleared"],
                                            form_refs=stats.get("form_refs"))
            paper = staged["candidate"]["paper"]
            run.say(f"  · 重新组装后可发布 {paper.get('questionCount')} 题")
        run.end("PROOFREAD_PAPER", detail)
    else:
        run.skip("PROOFREAD_PAPER", "本次未选文字模型")
    checkpoint()

    published: dict[str, Any] | None = None
    if stop_at_draft:
        run.skip("PUBLISH", "按要求停在待复核：组装已通过预检，去复核编辑器逐页签署后再发布")
        run.skip("EXPLAIN", "未发布，暂不写详解")
    else:
        run.begin("PUBLISH")
        detail, published = publish(run, workspace, manifest, staged, channel)
        run.end("PUBLISH", detail)
        checkpoint()
        if explain_profile and params.get("explain", True):
            run.begin("EXPLAIN")
            detail = explain(
                run, database, published_paper(database, published["paperVersionId"]) or paper,
                published["paperVersionId"], explain_profile, findings,
                int(params.get("explainLimit") or 0), cancelled,
                lambda done, total, failed=0: pages_progress("EXPLAIN")(done, total, failed))
            run.end("EXPLAIN", detail)
            # 题目已经发布了。详解是另一件事，结果里单独说，免得详解失败被读成整套失败。
            run.fact(explanations=detail)
        else:
            run.skip("EXPLAIN", "本次未选详解模型")
            run.fact(explanations="本次未选详解模型")

    result = {
        "steps": run.steps,
        "log": run.log[-LOG_LIMIT:],
        "sourceId": manifest["sourceId"],
        "workDir": str(work.relative_to(root)),
        "questionCount": paper.get("questionCount"),
        "completeness": paper.get("completeness"),
        "quality": quality,
        # 详解状态单列：详解失败不该让已经发布的题看起来整套都失败了。
        "explanations": run.facts.get("explanations"),
        "reviewGrade": paper.get("reviewGrade"),
        "attest": {k: stats.get(k) for k in
                   ("booklet_pages", "booklet_attested", "answer_pages", "answer_attested",
                    "unchanged", "contested", "slots_filled")},
        "attestErrors": (stats.get("errors") or [])[:20],
        "proofreadFindings": len(findings),
        "published": published,
        "reviewRequired": stop_at_draft or bool(findings) or bool(stats.get("errors")),
        **run.facts,
    }
    return result


def published_paper(database: Any, paper_version_id: str) -> dict[str, Any] | None:
    row = database.connection.execute(
        "SELECT payload_json FROM paper_versions WHERE id=?", (paper_version_id,)).fetchone()
    return json.loads(row[0]) if row and row[0] else None
