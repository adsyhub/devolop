"""Deterministically assemble reviewed page facts and an independent answer ledger."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .answers import answer_key
from .audit import audit_paper, prepare_paper
from .constants import FORM_SPECS, SCHEMA_VERSION
from .errors import ContractError, QualityGateError
from .page_contract import load_page_contracts
from .source import validate_source_manifest
from .util import load_json, stable_id, write_json


def _evidence(page: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceFileRole": page["sourceFileRole"],
        "page": page["page"],
        "bbox": list(block["bbox"]),
    }


def assemble_paper(
    *,
    manifest_path: Path,
    pages_dir: Path,
    answer_ledger_path: Path | None,
    output_path: Path,
) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_json(manifest_path)
    validate_source_manifest(manifest, manifest_path, verify_files=True)
    pages = load_page_contracts(pages_dir.expanduser().resolve())
    answers = load_json(answer_ledger_path.expanduser().resolve()) if answer_ledger_path else {"entries": {}}
    answer_entries = answers.get("entries")
    if not isinstance(answer_entries, dict):
        raise ContractError("Answer ledger entries must be an object")

    forms: dict[str, dict[str, Any]] = {}
    materials: dict[tuple[str, str, str], dict[str, Any]] = {}
    questions_seen: set[tuple[str, str]] = set()
    used_answers: set[str] = set()

    def form_for(code: str) -> dict[str, Any]:
        if code not in forms:
            spec = FORM_SPECS[code]
            forms[code] = {
                "formCode": code,
                "spec": spec.to_dict(),
                "groups": {},
            }
        return forms[code]

    def group_for(code: str, group_code: str) -> dict[str, Any]:
        form = form_for(code)
        groups = form["groups"]
        if group_code not in groups:
            groups[group_code] = {
                "groupId": stable_id("g_", manifest["sourceId"], code, group_code),
                "groupCode": group_code,
                "materials": [],
                "questions": [],
            }
        return groups[group_code]

    question_pages = [page for page in pages if page.get("sourceFileRole") == "QUESTION_BOOKLET"]
    for page in sorted(question_pages, key=lambda item: int(item["page"])):
        blocks = sorted(page.get("blocks", []), key=lambda block: int(block.get("readingOrder") or 0))
        for block in blocks:
            kind = block.get("kind")
            if kind == "material":
                form_code = str(block.get("formCode") or "")
                group_code = str(block.get("groupCode") or "")
                if form_code not in FORM_SPECS or not group_code:
                    raise ContractError(
                        f"Material {block.get('localKey')!r} on page {page['page']} needs formCode and groupCode"
                    )
                key = (form_code, group_code, str(block["localKey"]))
                if key not in materials:
                    material = {
                        "materialId": stable_id("m_", manifest["sourceId"], *key),
                        "localKey": key[2],
                        "contentAst": [],
                        "evidence": [],
                    }
                    materials[key] = material
                    group_for(form_code, group_code)["materials"].append(material)
                material = materials[key]
                material["contentAst"].extend(copy.deepcopy(block.get("contentAst") or []))
                material["evidence"].append(_evidence(page, block))
                continue
            if kind not in {"question", "writing-prompt"}:
                continue
            form_code = str(block["formCode"])
            group_code = str(block["groupCode"])
            local_key = str(block["localKey"])
            identity = (form_code, local_key)
            if identity in questions_seen:
                raise ContractError(f"Duplicate question localKey across pages: {form_code}/{local_key}")
            questions_seen.add(identity)
            answer_spec = copy.deepcopy(block["answerSpec"])
            answer_type = answer_spec["type"]
            correct_answer = None
            answer_ref = str(block.get("answerRef") or "")
            if answer_type != "ESSAY":
                ledger_key = answer_key(form_code, answer_ref)
                entry = answer_entries.get(ledger_key)
                if not isinstance(entry, dict):
                    raise ContractError(f"Answer ledger has no entry for {ledger_key}")
                if entry.get("answerType") != answer_type:
                    raise ContractError(
                        f"Answer type mismatch for {ledger_key}: page={answer_type}, key={entry.get('answerType')}"
                    )
                correct_answer = (
                    {"optionKey": str(entry["correctOption"])}
                    if answer_type == "SINGLE_CHOICE"
                    else {"tokens": {str(key): str(value) for key, value in entry["tokens"].items()}}
                )
                used_answers.add(ledger_key)
            question = {
                "questionId": stable_id("q_", manifest["sourceId"], form_code, local_key),
                "localKey": local_key,
                "printedLabel": block.get("printedLabel"),
                "sectionCode": str(block.get("sectionCode") or "MAIN"),
                "answerRef": answer_ref or None,
                "stemAst": copy.deepcopy(block.get("stemAst") or []),
                "options": copy.deepcopy(block.get("options") or []),
                "answerSpec": answer_spec,
                "correctAnswer": correct_answer,
                "materialRefs": list(block.get("materialRefs") or []),
                "evidence": [_evidence(page, block)],
            }
            group_for(form_code, group_code)["questions"].append(question)

    unused_answers = sorted(set(answer_entries) - used_answers)
    if unused_answers:
        raise ContractError(
            f"Answer ledger contains {len(unused_answers)} entries not used by question pages: {unused_answers[:12]}"
        )
    normalized_forms = []
    for code in forms:
        form = forms[code]
        form["groups"] = list(form["groups"].values())
        normalized_forms.append(form)
    if not normalized_forms:
        raise ContractError("No question blocks were assembled")
    paper = prepare_paper(
        {
            "schemaVersion": SCHEMA_VERSION,
            "examFamily": "EJU",
            "stableCode": manifest.get("inventoryId") or f"eju-{manifest['session'].lower()}-{manifest['subject'].lower()}-{manifest['language']}-" + "-".join(f["formCode"].lower() for f in normalized_forms),
            "title": f"{manifest['session']} EJU {manifest['subject']}",
            "session": manifest["session"],
            "syllabusVersion": manifest["syllabusVersion"],
            "source": {
                "sourceId": manifest["sourceId"],
                "rights": copy.deepcopy(manifest["rights"]),
                "files": copy.deepcopy(manifest["files"]),
                **({"inventoryId":manifest["inventoryId"]} if manifest.get("inventoryId") else {}),
            },
            "forms": normalized_forms,
        }
    )
    report = audit_paper(paper)
    if report["status"] != "passed":
        preview = "; ".join(f"{row['code']}: {row['message']}" for row in report["issues"][:10])
        raise QualityGateError(f"Assembled paper failed quality gate: {preview}")
    write_json(output_path.expanduser().resolve(), paper)
    return paper

