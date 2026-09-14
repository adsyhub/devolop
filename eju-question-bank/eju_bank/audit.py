"""Stable IDs, derived values and fail-closed paper quality gates."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Iterator

from .constants import ALLOWED_DIGIT_TOKENS, ANSWER_TYPES, COMPLETENESS_LEVELS, FORM_SPECS, SCHEMA_VERSION
from .page_contract import validate_ast
from .util import digest_json, stable_id


def iter_questions(paper: dict[str, Any]) -> Iterator[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    for form in paper.get("forms") or []:
        if not isinstance(form, dict):
            continue
        for group in form.get("groups") or []:
            if not isinstance(group, dict):
                continue
            for question in group.get("questions") or []:
                if isinstance(question, dict):
                    yield form, group, question


def prepare_paper(paper: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(paper)
    if "schemaVersion" not in prepared:
        prepared["schemaVersion"] = SCHEMA_VERSION
    if not prepared.get("paperId"):
        prepared["paperId"] = stable_id(
            "p_", prepared.get("stableCode"), prepared.get("session"), prepared.get("title")
        )
    sequence = 0
    for form, group, question in iter_questions(prepared):
        sequence += 1
        question["sequence"] = sequence
    prepared["questionCount"] = sequence

    # Default completeness
    if not prepared.get("completeness"):
        if sequence <= 5:
            prepared["completeness"] = "SAMPLE"
        else:
            prepared["completeness"] = "PARTIAL"

    if not prepared.get("availableModes"):
        prepared["availableModes"] = ["PRACTICE"]

    revision_fields = copy.deepcopy(prepared)
    revision_fields.pop("contentRevision", None)
    revision_fields.pop("createdAt", None)
    prepared["contentRevision"] = digest_json(revision_fields)
    return prepared


def _problem(issues: list[dict[str, Any]], code: str, message: str, ref: str | None = None) -> None:
    entry: dict[str, Any] = {"severity": "error", "code": code, "message": message}
    if ref:
        entry["ref"] = ref
    issues.append(entry)


def _audit_paper(paper: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    try:
        from .schema_validation import schema_issues
        for err in schema_issues("paper", paper):
            _problem(issues, err["code"], err["message"], err.get("ref"))
    except Exception:
        _problem(issues, "schema.unavailable", "Content validator is unavailable")

    schema_ver = paper.get("schemaVersion")
    if schema_ver not in {1, 2}:
        _problem(issues, "schema.unsupported", f"Expected schemaVersion 1 or 2, got {schema_ver}.")
    if paper.get("examFamily") != "EJU":
        _problem(issues, "paper.family_invalid", "examFamily must be EJU.")
    if not str(paper.get("title") or "").strip():
        _problem(issues, "paper.title_missing", "Paper title is required.")
    if not str(paper.get("session") or "").strip():
        _problem(issues, "paper.session_missing", "Paper session is required.")
    source = paper.get("source")
    if not isinstance(source, dict) or not str(source.get("sourceId") or ""):
        _problem(issues, "paper.source_missing", "Paper source provenance is required.")
    forms = paper.get("forms")
    if not isinstance(forms, list) or not forms:
        _problem(issues, "paper.forms_missing", "Paper needs at least one form.")
        forms = []

    completeness = paper.get("completeness", "SAMPLE")
    if completeness not in COMPLETENESS_LEVELS:
        _problem(issues, "paper.completeness_invalid", f"Invalid completeness level {completeness!r}.")

    form_codes: list[str] = []
    question_ids: list[str] = []
    answer_refs: list[str] = []
    figure_count = 0

    for form in forms:
        if not isinstance(form, dict):
            _problem(issues, "form.not_object", "Form must be an object.")
            continue
        code = str(form.get("formCode") or "")
        form_codes.append(code)
        if code not in FORM_SPECS:
            _problem(issues, "form.code_invalid", f"Unknown formCode {code!r}.", code)
        groups = form.get("groups")
        if not isinstance(groups, list) or not groups:
            _problem(issues, "form.groups_missing", "Form needs at least one group.", code)
            continue
        for group in groups:
            group_code = str(group.get("groupCode") or "?")
            ref = f"{code}/{group_code}"
            if not isinstance(group.get("questions"), list) or not group["questions"]:
                _problem(issues, "group.questions_missing", "Group needs at least one question.", ref)
            material_keys = {
                str(material.get("localKey"))
                for material in group.get("materials") or []
                if isinstance(material, dict)
            }
            for material in group.get("materials") or []:
                if not isinstance(material, dict):
                    _problem(issues, "material.not_object", "Material must be an object.", ref)
                    continue
                for ast_issue in validate_ast(material.get("contentAst"), ref=ref + "/material"):
                    _problem(issues, ast_issue["code"], ast_issue["message"], ast_issue.get("ref"))
                for node in material.get("contentAst") or []:
                    if isinstance(node, dict) and node.get("type") == "figure":
                        figure_count += 1
                        if completeness == "COMPLETE" and not node.get("assetId"):
                            _problem(
                                issues,
                                "figure.asset_missing",
                                "Figure in COMPLETE paper must have a resolved assetId.",
                                ref + "/material",
                            )

            for question in group.get("questions") or []:
                if not isinstance(question, dict):
                    _problem(issues, "question.not_object", "Question must be an object.", ref)
                    continue
                question_id = str(question.get("questionId") or "")
                question_ids.append(question_id)
                qref = question_id or ref
                if not question_id:
                    _problem(issues, "question.id_missing", "questionId is required.", qref)
                for ast_issue in validate_ast(question.get("stemAst"), ref=qref + "/stem"):
                    _problem(issues, ast_issue["code"], ast_issue["message"], ast_issue.get("ref"))
                for node in question.get("stemAst") or []:
                    if isinstance(node, dict) and node.get("type") == "figure":
                        figure_count += 1
                        if completeness == "COMPLETE" and not node.get("assetId"):
                            _problem(
                                issues,
                                "figure.asset_missing",
                                "Figure in COMPLETE paper must have a resolved assetId.",
                                qref + "/stem",
                            )

                for material_ref in question.get("materialRefs") or []:
                    if str(material_ref) not in material_keys:
                        _problem(
                            issues,
                            "question.material_missing",
                            f"Unknown material localKey {material_ref!r}.",
                            qref,
                        )
                answer_spec = question.get("answerSpec")
                answer_type = answer_spec.get("type") if isinstance(answer_spec, dict) else None
                if answer_type not in ANSWER_TYPES:
                    _problem(issues, "question.answer_type_invalid", "Invalid answer type.", qref)
                    continue
                correct = question.get("correctAnswer")
                if answer_type == "SINGLE_CHOICE":
                    options = question.get("options")
                    keys = [str(option.get("key")) for option in options or [] if isinstance(option, dict)]
                    if len(keys) < 2 or len(keys) != len(set(keys)):
                        _problem(issues, "question.options_invalid", "Options need unique keys and count >= 2.", qref)
                    correct_key = str(correct.get("optionKey")) if isinstance(correct, dict) else ""
                    if correct_key not in keys:
                        _problem(issues, "question.correct_option_invalid", "Correct option is not present.", qref)
                elif answer_type == "DIGIT_GRID":
                    slots = [str(slot) for slot in answer_spec.get("slots") or []]
                    tokens = correct.get("tokens") if isinstance(correct, dict) else None
                    if not slots or len(slots) != len(set(slots)):
                        _problem(issues, "question.digit_slots_invalid", "Digit-grid slots are missing/duplicate.", qref)
                    if not isinstance(tokens, dict) or set(tokens) != set(slots):
                        _problem(issues, "question.digit_answer_mismatch", "Digit answer must cover exact slots.", qref)
                    elif any(str(token) not in ALLOWED_DIGIT_TOKENS for token in tokens.values()):
                        _problem(issues, "question.digit_token_invalid", "Digit answer contains invalid token.", qref)
                elif answer_type == "ESSAY":
                    if correct is not None:
                        _problem(issues, "question.essay_has_key", "Essay must not have a unique correct answer.", qref)
                answer_ref = question.get("answerRef")
                if answer_type != "ESSAY":
                    if not answer_ref:
                        _problem(issues, "question.answer_ref_missing", "Objective question needs answerRef.", qref)
                    answer_refs.append(f"{code}|{answer_ref}")
                evidence = question.get("evidence")
                if not isinstance(evidence, list) or not evidence:
                    _problem(issues, "question.evidence_missing", "Source-page evidence is required.", qref)

    for value, count in Counter(form_codes).items():
        if value and count > 1:
            _problem(issues, "form.duplicate", f"Duplicate formCode {value}.")
    for value, count in Counter(question_ids).items():
        if value and count > 1:
            _problem(issues, "question.id_duplicate", f"Duplicate questionId {value}.")
    for value, count in Counter(answer_refs).items():
        if value and count > 1:
            _problem(issues, "question.answer_ref_duplicate", f"Duplicate answer reference {value}.")

    question_count = sum(1 for _ in iter_questions(paper))
    if paper.get("questionCount") != question_count:
        _problem(
            issues,
            "paper.question_count_wrong",
            f"questionCount={paper.get('questionCount')} but found {question_count}.",
        )

    modes = paper.get("availableModes", ["PRACTICE"])
    if not isinstance(modes, list) or not modes or any(mode not in {"PRACTICE", "SECTION", "MOCK"} for mode in modes):
        _problem(issues, "paper.modes_invalid", "Invalid availableModes")
    elif completeness != "COMPLETE" and "MOCK" in modes:
        _problem(issues, "paper.partial_mock", "Only COMPLETE papers may enable MOCK")
    for ref, node in iter_asset_nodes(paper):
        asset_id = node.get("assetId")
        if not isinstance(asset_id, str) or len(asset_id) != 64 or any(c not in "0123456789abcdef" for c in asset_id):
            _problem(issues, "figure.asset_invalid", "Published media requires a resolved SHA-256 asset ID", ref)
    for form, group, question in iter_questions(paper):
        for index, option in enumerate(question.get("options") or []):
            for entry in validate_ast(option.get("contentAst"), ref=f"{question['questionId']}/option/{index}"):
                _problem(issues, entry["code"], entry["message"], entry.get("ref"))
    if completeness == "COMPLETE" and paper.get("contentKind") != "SYNTHETIC":
        review = paper.get("reviewSummary") or {}
        if review.get("status") != "REVIEWED" or not review.get("reviewId") or review.get("contentDigest") != review_content_digest(paper):
            _problem(issues, "review.required", "Complete source papers require a signed review bound to this content")
        expected = paper.get("expectedStructure") or {}
        expected_forms = expected.get("forms")
        actual_forms = {f["formCode"]: [q.get("answerRef") or q["questionId"] for ff, _, q in iter_questions(paper) if ff is f] for f in forms}
        if expected_forms != actual_forms:
            _problem(issues, "paper.structure_mismatch", "Forms and ordered question references must match the reviewed source baseline")
        pages = expected.get("pages")
        if not isinstance(pages, dict) or not pages or not all(type(n) is int and n > 0 for n in pages.values()):
            _problem(issues, "paper.pages_missing", "Expected source page counts are required")

    return {
        "status": "passed" if not issues else "failed",
        "summary": {
            "questions": question_count,
            "forms": len(forms),
            "errors": len(issues),
            "completeness": completeness,
            "issueCounts": dict(Counter(item["code"] for item in issues)),
        },
        "issues": issues,
    }


def iter_asset_nodes(value, ref="paper"):
    if isinstance(value, dict):
        if value.get("type") == "figure" or value.get("assetId"):
            yield ref, value
        for key, child in value.items():
            yield from iter_asset_nodes(child, f"{ref}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_asset_nodes(child, f"{ref}/{index}")


def review_content_digest(paper):
    payload = copy.deepcopy(paper)
    for key in ("reviewSummary", "contentRevision", "createdAt"):
        payload.pop(key, None)
    return digest_json(payload)


def audit_paper(paper):
    try:
        if not isinstance(paper, dict):
            raise TypeError("Paper must be an object")
        return _audit_paper(paper)
    except (TypeError, KeyError, ValueError, AttributeError):
        return {"status": "failed", "summary": {"errors": 1}, "issues": [
            {"severity": "error", "code": "paper.invalid_structure", "message": "Malformed nested paper structure"}]}


def delivery_paper(paper: dict[str, Any]) -> dict[str, Any]:
    """Return learner-safe content with all correct answers removed."""
    delivery = copy.deepcopy(paper)
    for _, _, question in iter_questions(delivery):
        question.pop("correctAnswer", None)
    source = delivery.get("source")
    if isinstance(source, dict):
        for file_entry in source.get("files") or []:
            if isinstance(file_entry, dict):
                file_entry.pop("path", None)
        rights = source.get("rights")
        if isinstance(rights, dict):
            rights.pop("note", None)
    return delivery
