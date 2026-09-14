"""制课：一条任务把上传的 PDF 做成可练的卷。

这里测的是编排与闸门，不是模型质量：模型全部关掉，只留确定性的那几步
（登记 → 探测 → 渲染 → 页面合同与机器校验 → 组装 → 发布）。带模型的两步
（校对复读、真题详解）另测参数校验，跑不跑得动取决于本机有没有起推理服务。
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request

import pytest

from eju_bank.errors import ContractError
from eju_bank.paper_naming import describe
from eju_bank.uploads import resolve, store


def test_filename_detection_reports_what_it_could_not_read():
    booklet = describe("2023平成35年第2回数学2.pdf")
    assert (booklet["session"], booklet["subject"], booklet["course"]) == (
        "2023-2", "MATHEMATICS", "COURSE_2")
    assert booklet["role"] == "QUESTION_BOOKLET"
    assert booklet["needsConfirmation"] == []

    # 理综和日语的答案册文件名里没有科目。猜一个比留空危险，所以它必须留空并说出来。
    answer = describe("2002平成14年第1回答案.pdf")
    assert answer["role"] == "ANSWER_KEY"
    assert answer["subject"] is None
    assert "subject" in answer["needsConfirmation"]
    assert answer["inventoryId"] is None


def test_upload_only_accepts_real_pdfs_and_stays_in_the_workspace(tmp_path):
    saved = store(tmp_path, "2016年第1回理科.pdf", b"%PDF-1.7\nbody")
    assert saved["uploadId"].startswith("incoming/")
    assert resolve(tmp_path, saved["uploadId"]).is_file()
    # 同一份内容重复上传不堆第二个文件。
    assert store(tmp_path, "2016年第1回理科.pdf", b"%PDF-1.7\nbody")["uploadId"] == saved["uploadId"]

    with pytest.raises(ContractError):
        store(tmp_path, "x.pdf", b"not a pdf at all")
    for bad in ["../../etc/passwd", "/etc/passwd", "work/x.pdf", "incoming/../../x"]:
        with pytest.raises(ContractError):
            resolve(tmp_path, bad)


def test_vision_profiles_must_stay_on_loopback(tmp_path):
    from eju_bank import model_profiles
    (tmp_path / "config").mkdir()
    (tmp_path / "config/providers.json").write_text(json.dumps({
        "visionProfiles": {"leaky": {"baseUrl": "https://api.example.com/v1", "model": "m"}},
        "textProfiles": {"hosted": {"baseUrl": "https://api.example.com/v1", "model": "m",
                                    "apiKeyEnv": "EXAMPLE_KEY"},
                         "sneaky": {"baseUrl": "https://api.example.com/v1", "model": "m"}},
    }), encoding="utf-8")
    loaded = model_profiles.load_profiles(tmp_path)
    # 原页图不出本机：视觉档位没有云端这条路。
    assert "leaky" not in loaded["vision"]
    assert "leaky" in loaded["problems"]
    # 文字档位可以走云端，但配置所有者必须显式写出取密钥的环境变量名。
    assert "hosted" in loaded["text"]
    assert "sneaky" not in loaded["text"]
    with pytest.raises(ContractError):
        model_profiles.resolve(tmp_path, "vision", "leaky")


def _studio_workspace(tmp_path):
    """一个能走完确定性流水线的最小工作区。"""
    import pymupdf
    from eju_bank.server import create_server

    for folder in ("incoming", "content", "config", "library"):
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    (tmp_path / "config/providers.json").write_text('{"providers":{}}', encoding="utf-8")
    (tmp_path / "content/content-inventory.json").write_text(
        '{"schemaVersion":1,"updatedAt":"2026-01-01T00:00:00Z","items":[]}', encoding="utf-8")
    for name in ("booklet.pdf", "answers.pdf"):
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 96), "EJU fixture " + name)
        doc.save(tmp_path / "incoming" / name)
        doc.close()
    return create_server(tmp_path / "library/eju.db", port=0, workspace_root=tmp_path,
                         start_worker=False)


def test_make_paper_rejects_requests_the_pipeline_could_not_honour(tmp_path):
    server = _studio_workspace(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        data = (tmp_path / "incoming/booklet.pdf").read_bytes()
        request = urllib.request.Request(
            base + "/api/v1/admin/uploads", data=data, method="POST",
            headers={"Content-Type": "application/pdf",
                     "X-Upload-Filename": urllib.parse.quote("2016年第1回理科.pdf")})
        with urllib.request.urlopen(request, timeout=20) as response:
            upload = json.load(response)
        assert upload["detected"]["subject"] == "SCIENCE"

        def make(body):
            request = urllib.request.Request(
                base + "/api/v1/admin/papers", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)

        good = {"questionBooklet": upload["uploadId"], "session": "2016-1",
                "subject": "SCIENCE", "language": "ja", "ocrProfile": "local-glm-ocr"}
        for field, value, reason in [
            ("session", "2016", "回次格式"),
            ("subject", "PHYSICS", "不存在的科目"),
            ("questionBooklet", "../../etc/passwd", "路径穿越"),
            ("ocrProfile", "made-up", "未定义的档位"),
            ("channel", "PUBLIC", "私人题库以外的发布渠道"),
        ]:
            status, body = make({**good, field: value})
            assert status == 422, f"{reason} 应被拒绝，却返回 {status}"
            assert body["error"]["message"]

        # 数学必须说清是 1 类还是 2 类：两类是不同的卷。
        status, _ = make({**good, "subject": "MATHEMATICS"})
        assert status == 422
        # 别的科目不能带类别。
        status, _ = make({**good, "course": "COURSE_1"})
        assert status == 422

        # 参数齐了就排进队列，任务类型与目标清单条目都对得上。
        status, job = make(good)
        assert status == 202, job
        assert job["jobType"] == "MAKE_PAPER"
        assert job["targetId"] == "eju-2016-1-science-ja"
        assert job["status"] == "QUEUED"
        # 同样的请求不会排出第二条任务。
        assert make(good)[1]["jobId"] == job["jobId"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.database.close()
