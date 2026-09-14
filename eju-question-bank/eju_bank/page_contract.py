"""Validation for model/human-authored per-page facts."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from .constants import (
    ALLOWED_DIGIT_TOKENS,
    ANSWER_TYPES,
    AST_NODE_TYPES,
    BLOCK_KINDS,
    FORM_SPECS,
    PAGE_CONTRACT_VERSION,
)
from .errors import ContractError
from .schema_validation import schema_issues
from .util import load_json

_SLOT_PATTERN = re.compile(r"^[A-Z]$")
_UNSAFE_TEXT = re.compile(r"<\s*/?\s*(?:script|iframe|object|embed|style|link)\b", re.I)


def issue(code: str, message: str, ref: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"code": code, "message": message}
    if ref:
        value["ref"] = ref
    return value


def valid_bbox(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    if not all(type(number) in (int, float) for number in value):
        return False
    x0, y0, x1, y1 = (float(number) for number in value)
    return 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1


def validate_ast(nodes: Any, *, ref: str, depth=0) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if depth>40:return [issue("ast.depth","AST nesting limit exceeded",ref)]
    if not isinstance(nodes, list):
        return [issue("ast.not_array", "Content AST must be an array.", ref)]
    for index, node in enumerate(nodes):
        node_ref = f"{ref}.ast[{index}]"
        if not isinstance(node, dict):
            issues.append(issue("ast.node_not_object", "AST node must be an object.", node_ref))
            continue
        node_type = str(node.get("type") or "")
        if node_type not in AST_NODE_TYPES:
            issues.append(issue("ast.type_invalid", f"Unsupported AST node type {node_type!r}.", node_ref))
            continue
        if node_type in {"text", "paragraph", "callout", "underline"}:
            text = str(node.get("value") or "")
            if not text:
                issues.append(issue("ast.text_empty", "Text node must not be empty.", node_ref))
            if _UNSAFE_TEXT.search(text):
                issues.append(issue("ast.unsafe_markup", "Executable HTML is not allowed.", node_ref))
        elif node_type in {"inlineMath", "displayMath"}:
            if not str(node.get("latex") or "").strip():
                issues.append(issue("ast.latex_empty", "Math node needs non-empty LaTeX.", node_ref))
        elif node_type == "figure":
            if not str(node.get("assetId") or "").strip() and not valid_bbox(node.get("sourceBbox")):
                issues.append(
                    issue(
                        "ast.figure_source_missing",
                        "Figure needs an assetId or a normalized sourceBbox.",
                        node_ref,
                    )
                )
        elif node_type == "table":
            rows = node.get("rows")
            if not isinstance(rows, list) or not rows:
                issues.append(issue("ast.table_empty", "Table needs at least one row.", node_ref))
            else:
                for row in rows:
                    if not isinstance(row,list):issues.append(issue('ast.table_row','Table row must be an array',node_ref));continue
                    for cell in row:
                        if isinstance(cell,list):issues.extend(validate_ast(cell,ref=node_ref,depth=depth+1))
                        elif isinstance(cell,dict):issues.extend(validate_ast(cell.get('contentAst',[cell]),ref=node_ref,depth=depth+1))
                        elif not isinstance(cell,str):issues.append(issue('ast.table_cell','Invalid table cell',node_ref))
        elif node_type == "answerSlot":
            if not _SLOT_PATTERN.fullmatch(str(node.get("slot") or "")):
                issues.append(issue("ast.slot_invalid", "Answer slot must be one letter A-Z.", node_ref))
        elif node_type == "ruby":
            if not str(node.get("base") or "") or not str(node.get("ruby") or ""):
                issues.append(issue("ast.ruby_invalid", "Ruby node needs base and ruby text.", node_ref))
        children = node.get("children")
        if children is not None:
            issues.extend(validate_ast(children, ref=node_ref + ".children", depth=depth+1))
    return issues


def validate_answer_spec(spec: Any, *, ref: str, options: Any = None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not isinstance(spec, dict):
        return [issue("answer_spec.not_object", "answerSpec must be an object.", ref)]
    answer_type = str(spec.get("type") or "")
    if answer_type not in ANSWER_TYPES:
        return [issue("answer_spec.type_invalid", f"Unsupported answer type {answer_type!r}.", ref)]
    if answer_type == "SINGLE_CHOICE":
        if not isinstance(options, list) or len(options) < 2:
            issues.append(issue("choice.options_too_few", "Single-choice question needs at least two options.", ref))
        else:
            keys = [str(item.get("key") or "") for item in options if isinstance(item, dict)]
            if len(keys) != len(options) or any(not key for key in keys):
                issues.append(issue("choice.option_key_missing", "Every option needs a key.", ref))
            if len(set(keys)) != len(keys):
                issues.append(issue("choice.option_key_duplicate", "Option keys must be unique.", ref))
    elif answer_type == "DIGIT_GRID":
        slots = spec.get("slots")
        if not isinstance(slots, list) or not slots:
            issues.append(issue("digit_grid.slots_missing", "Digit grid needs one or more slots.", ref))
        else:
            values = [str(slot) for slot in slots]
            if any(not _SLOT_PATTERN.fullmatch(value) for value in values):
                issues.append(issue("digit_grid.slot_invalid", "Every slot must be one letter A-Z.", ref))
            if len(values) != len(set(values)):
                issues.append(issue("digit_grid.slot_duplicate", "Digit-grid slots must be unique.", ref))
        allowed = spec.get("allowedTokens", list(ALLOWED_DIGIT_TOKENS))
        if not isinstance(allowed, list) or any(str(token) not in ALLOWED_DIGIT_TOKENS for token in allowed):
            issues.append(issue("digit_grid.token_invalid", "Allowed tokens may only be '-' or 0-9.", ref))
    elif answer_type == "ESSAY":
        if not str(spec.get("rubricId") or "").strip():
            issues.append(issue("essay.rubric_missing", "Essay answerSpec needs rubricId.", ref))
    return issues


def validate_page_contract(page: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    # Structural JSON Schema validation
    try:
        for err in schema_issues("page-contract", page):
            issues.append(issue(err["code"], err["message"], err.get("ref")))
    except Exception as exc:
        issues.append(issue("schema.error", f"Schema validation failed: {exc}"))

    if not isinstance(page,dict): return {"status":"failed","issues":issues}
    schema_ver = page.get("schemaVersion")
    if schema_ver not in {1, 2}:
        issues.append(issue("page.schema_unsupported", f"Expected schemaVersion 1 or 2, got {schema_ver}."))
    page_number = page.get("page")
    if type(page_number) is not int or page_number < 1:
        issues.append(issue("page.number_invalid", "page must be a positive integer."))
    if page.get("sourceFileRole") not in {"QUESTION_BOOKLET", "ANSWER_KEY"}:
        issues.append(issue("page.role_invalid", "sourceFileRole must identify a PDF role."))
    blocks = page.get("blocks")
    if not isinstance(blocks, list):
        issues.append(issue("page.blocks_not_array", "blocks must be an array."))
        blocks = []
    local_keys: set[str] = set()
    for index, block in enumerate(blocks):
        ref = f"page:{page_number}:block:{index}"
        if not isinstance(block, dict):
            issues.append(issue("block.not_object", "Block must be an object.", ref))
            continue
        kind = str(block.get("kind") or "")
        if kind not in BLOCK_KINDS:
            issues.append(issue("block.kind_invalid", f"Unsupported block kind {kind!r}.", ref))
            continue
        if not valid_bbox(block.get("bbox")):
            issues.append(issue("block.bbox_invalid", "Block needs normalized bbox [x0,y0,x1,y1].", ref))
        local_key = str(block.get("localKey") or "")
        if local_key:
            if local_key in local_keys:
                issues.append(issue("block.local_key_duplicate", f"Duplicate localKey {local_key!r} on page.", ref))
            local_keys.add(local_key)
        if kind in {"question", "writing-prompt"}:
            if not local_key:
                issues.append(issue("question.local_key_missing", "Question needs stable localKey.", ref))
            form_code = str(block.get("formCode") or "")
            if form_code not in FORM_SPECS:
                issues.append(issue("question.form_invalid", f"Unknown formCode {form_code!r}.", ref))
            if not str(block.get("groupCode") or "").strip():
                issues.append(issue("question.group_missing", "Question needs groupCode.", ref))
            issues.extend(validate_ast(block.get("stemAst"), ref=ref + ".stem"))
            options = block.get("options", [])
            if isinstance(options, list):
                for option_index, option in enumerate(options):
                    if not isinstance(option, dict):
                        issues.append(issue("choice.option_not_object", "Option must be an object.", ref))
                        continue
                    issues.extend(
                        validate_ast(option.get("contentAst"), ref=f"{ref}.options[{option_index}]")
                    )
            issues.extend(validate_answer_spec(block.get("answerSpec"), ref=ref, options=options))
            if kind == "question" and (block.get("answerSpec") or {}).get("type") != "ESSAY":
                if not str(block.get("answerRef") or "").strip():
                    issues.append(issue("question.answer_ref_missing", "Objective question needs answerRef.", ref))
        elif kind == "material":
            if not local_key:
                issues.append(issue("material.local_key_missing", "Material needs stable localKey.", ref))
            issues.extend(validate_ast(block.get("contentAst"), ref=ref + ".content"))
        elif kind == "answer-entry":
            if str(block.get("formCode") or "") not in FORM_SPECS:
                issues.append(issue("answer_entry.form_invalid", "Answer entry needs valid formCode.", ref))
            if not str(block.get("answerRef") or "").strip():
                issues.append(issue("answer_entry.ref_missing", "Answer entry needs answerRef.", ref))
            answer_type = str(block.get("answerType") or "")
            if answer_type not in {"SINGLE_CHOICE", "DIGIT_GRID"}:
                issues.append(issue("answer_entry.type_invalid", "Answer entry type is invalid.", ref))

    coverage = page.get("coverage")
    if not isinstance(coverage, dict):
        issues.append(issue("page.coverage_missing", "coverage object is required."))
    else:
        ink = coverage.get("inkRegions")
        accounted = coverage.get("accountedRegions")
        if type(ink) is not int or ink < 0 or type(accounted) is not int or accounted < 0:
            issues.append(issue("page.coverage_invalid", "Coverage counts must be non-negative integers."))
        elif accounted != ink:
            issues.append(
                issue(
                    "page.coverage_incomplete",
                    f"Only {accounted} of {ink} ink regions are accounted for.",
                )
            )

        region_ids = coverage.get("regionIds")
        accounted_ids = coverage.get("accountedRegionIds")
        if region_ids is not None or accounted_ids is not None:
            if not isinstance(region_ids, list) or not isinstance(accounted_ids, list):
                issues.append(issue("page.coverage_invalid", "regionIds and accountedRegionIds must be lists."))
            elif not all(isinstance(r,str) and r for r in region_ids + accounted_ids):
                issues.append(issue('page.coverage_invalid','Region IDs must be nonempty strings'))
            else:
                if len(region_ids)!=ink or len(accounted_ids)!=accounted:
                    issues.append(issue('page.coverage_count_mismatch','Region counts do not match the declared sets'))
                set_region = set(region_ids)
                set_accounted = set(accounted_ids)
                if len(set_region) != len(region_ids):
                    issues.append(issue("page.coverage_duplicate_regions", "regionIds contains duplicate IDs."))
                if len(set_accounted) != len(accounted_ids):
                    issues.append(issue("page.coverage_duplicate_regions", "accountedRegionIds contains duplicate IDs."))
                if set_region != set_accounted:
                    diff_missing = sorted(list(set_region - set_accounted))
                    diff_extra = sorted(list(set_accounted - set_region))
                    diff_desc = []
                    if diff_missing:
                        diff_desc.append(f"missing {diff_missing[:5]}")
                    if diff_extra:
                        diff_desc.append(f"extra {diff_extra[:5]}")
                    issues.append(
                        issue(
                            "page.coverage_regions_mismatch",
                            f"Region sets do not match: {', '.join(diff_desc)}.",
                        )
                    )
    return {"status": "passed" if not issues else "failed", "issues": issues}


def migrate_page_contract_v1_to_v2(contract: dict[str, Any]) -> dict[str, Any]:
    """Pure function migrating a v1 page contract to v2 while preserving evidence."""
    v2 = copy.deepcopy(contract)
    v2["schemaVersion"] = 2
    coverage = v2.setdefault("coverage", {"inkRegions": 0, "accountedRegions": 0})
    if "regionIds" not in coverage:
        v2["needsReview"] = True
    v2.setdefault("issues", [])
    return v2


def validate_learner_response(question: dict[str, Any], response: Any) -> None:
    """Strictly validates learner response type, slots and character length (EJU-009)."""
    if not isinstance(response, dict):
        raise ContractError("Response must be a JSON object")
    ans_type = question.get("answerSpec", {}).get("type")
    res_type = response.get("type")
    if res_type != ans_type:
        raise ContractError(f"Response type mismatch: expected {ans_type}, got {res_type}")

    if ans_type == "SINGLE_CHOICE":
        opt = response.get("optionKey", "")
        if not isinstance(opt, str):
            raise ContractError("optionKey must be a string")
        valid_keys = {str(item.get("key")) for item in question.get("options") or []}
        if opt and opt not in valid_keys:
            raise ContractError(f"Invalid optionKey {opt!r}; allowed options: {sorted(valid_keys)}")
    elif ans_type == "DIGIT_GRID":
        slots = [str(s) for s in question.get("answerSpec", {}).get("slots") or []]
        tokens = response.get("tokens")
        if not isinstance(tokens, dict):
            raise ContractError("Digit grid response must have tokens dictionary")
        for slot, tok in tokens.items():
            if slot not in slots:
                raise ContractError(f"Invalid slot {slot!r} in response; question slots: {slots}")
            if not isinstance(tok, str) or tok not in ALLOWED_DIGIT_TOKENS:
                raise ContractError(f"Invalid token {tok!r} in slot {slot}; allowed: '-' or 0-9")
    elif ans_type == "ESSAY":
        text = response.get("text")
        if not isinstance(text, str):
            raise ContractError("Essay text must be a string")
        if text and len(text) > 10_000:
            raise ContractError(f"Essay text length ({len(text)}) exceeds maximum allowed (10,000 chars)")


def load_page_contracts(pages_dir: Path, *, require_valid: bool = True) -> list[dict[str, Any]]:
    files = [p for p in sorted(pages_dir.glob("p*.json")) if not p.name.endswith(".cache.json")]
    if not files:
        raise ContractError(f"No page contracts found in {pages_dir}")
    pages = []
    seen: set[tuple[str, int]] = set()
    all_issues = []
    for path in files:
        page = load_json(path)
        if not isinstance(page, dict):
            raise ContractError(f"Page contract must be an object: {path}")
        key = (str(page.get("sourceFileRole")), int(page.get("page") or 0))
        if key in seen:
            raise ContractError(f"Duplicate page contract for {key[0]} page {key[1]}")
        seen.add(key)
        report = validate_page_contract(page)
        if report["status"] != "passed":
            all_issues.extend({**entry, "file": str(path)} for entry in report["issues"])
        pages.append(page)
    if require_valid and all_issues:
        preview = "; ".join(f"{item['code']}: {item['message']}" for item in all_issues[:8])
        raise ContractError(f"Invalid page contracts ({len(all_issues)} issues): {preview}")
    return sorted(pages, key=lambda item: (str(item.get("sourceFileRole")), int(item["page"])))


def empty_page_contract(page: int, role: str) -> dict[str, Any]:
    return {
        "schemaVersion": PAGE_CONTRACT_VERSION,
        "page": page,
        "sourceFileRole": role,
        "blocks": [],
        "coverage": {"inkRegions": 0, "accountedRegions": 0},
        "issues": [],
    }
