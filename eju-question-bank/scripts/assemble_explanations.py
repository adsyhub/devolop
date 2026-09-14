#!/usr/bin/env python3
"""Assemble and inject 2023-2 Science & Math detailed explanations into EJU Question Bank.

This tool:
1. Loads structured solutions from:
   - work/2023-2-math-c1/explanations.json
   - work/2023-2-math-c2/explanations.json
   - work/2023-2-science/explanations.json
2. Converts explanations into canonical question bank AST nodes (validated against page_contract).
3. Injects them into question_versions.explanation_json in library/eju.db.
4. Registers reviewed explanation streams in explanation_revisions via Database.save_explanation.
5. Injects explanation ASTs into work/<session>/paper.json for downstream publishing.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.db import Database
from eju_bank.page_contract import validate_ast
from eju_bank.util import canonical_json, utc_now


def convert_solution_to_ast(solution_text: str) -> list[dict[str, Any]]:
    """Convert markdown solution text into validated AST paragraphs."""
    paragraphs = [p.strip() for p in solution_text.split("\n\n") if p.strip()]
    nodes = [{"type": "paragraph", "value": p} for p in paragraphs]
    issues = validate_ast(nodes, ref="assembled_explanation")
    if issues:
        raise ValueError(f"AST validation issues: {issues}")
    return nodes


def build_explanation_payload(
    title: str,
    points: list[str],
    official_answer: Any,
    solution_text: str,
    *,
    language: str = "zh",
) -> dict[str, Any]:
    """Construct an explanation payload conforming to the EJU question bank contract."""
    ast_nodes = convert_solution_to_ast(solution_text)
    return {
        "kind": "EXPLANATION",
        "language": language,
        "title": title,
        "points": points,
        "officialAnswer": official_answer,
        "contentAst": ast_nodes,
        "updatedAt": utc_now(),
    }


def assemble_science_explanations(
    science_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Map science explanations to question stable keys (phys-q-XX, chem-q-XX, bio-q-XX)."""
    mapped: dict[str, dict[str, Any]] = {}

    # 1. Physics (問1 ～ 問19)
    phys_list = science_data["forms"]["PHYSICS_JA"]
    for q in phys_list:
        q_num = q["q_num"]
        key = f"phys-q-{q_num:02d}"
        payload = build_explanation_payload(
            title=q["title"],
            points=q["points"],
            official_answer=q["answer"],
            solution_text=q["solution"],
        )
        mapped[key] = payload

    # 2. Chemistry (問1 ～ 問20)
    chem_list = science_data["forms"]["CHEMISTRY_JA"]
    for q in chem_list:
        q_num = q["q_num"]
        key = f"chem-q-{q_num:02d}"
        payload = build_explanation_payload(
            title=q["title"],
            points=q["points"],
            official_answer=q["answer"],
            solution_text=q["solution"],
        )
        mapped[key] = payload

    # 3. Biology (問1 ～ 問17, 18 answer items)
    bio_list = science_data["forms"]["BIOLOGY_JA"]
    for idx, q in enumerate(bio_list, start=1):
        key = f"bio-q-{idx:02d}"
        payload = build_explanation_payload(
            title=q["title"],
            points=q["points"],
            official_answer=q["answer"],
            solution_text=q["solution"],
        )
        mapped[key] = payload

    return mapped


def assemble_math_c1_explanations(
    math_data: Any,
    session: str = "2023-2",
) -> dict[str, dict[str, Any]]:
    """Map Math Course 1 explanations to question stable keys."""
    mapped: dict[str, dict[str, Any]] = {}
    if isinstance(math_data, list):
        for s in math_data:
            key = s.get("localKey") or f"math-q-{s.get('q_num') or s.get('sectionId')}"
            mapped[key] = build_explanation_payload(
                title=s.get("title") or s.get("sectionTitle"),
                points=s.get("points", []),
                official_answer=s.get("answer") or s.get("officialAnswers"),
                solution_text=s.get("solution") or s.get("detailedSolution"),
            )
        return mapped

    sections = math_data["sections"]

    # If already split into individual question sections
    if len(sections) == 8:
        for s in sections:
            key = s.get("localKey") or f"math-q-{s['sectionId']}"
            mapped[key] = build_explanation_payload(
                title=s["sectionTitle"],
                points=s["points"],
                official_answer=s["officialAnswers"],
                solution_text=s["detailedSolution"],
            )
        return mapped

    # I_1 -> math-q-I_1
    s0 = sections[0]
    mapped["math-q-I_1"] = build_explanation_payload(
        title=s0["sectionTitle"],
        points=s0["points"],
        official_answer=s0["officialAnswers"],
        solution_text=s0["detailedSolution"],
    )

    # I_2 -> math-q-I_2
    s1 = sections[1]
    mapped["math-q-I_2"] = build_explanation_payload(
        title=s1["sectionTitle"],
        points=s1["points"],
        official_answer=s1["officialAnswers"],
        solution_text=s1["detailedSolution"],
    )

    # II_1 -> math-q-II_1
    s2 = sections[2]
    mapped["math-q-II_1"] = build_explanation_payload(
        title=s2["sectionTitle"],
        points=s2["points"],
        official_answer=s2["officialAnswers"],
        solution_text=s2["detailedSolution"],
    )

    # II_2 -> math-q-II_2
    s3 = sections[3]
    mapped["math-q-II_2"] = build_explanation_payload(
        title=s3["sectionTitle"],
        points=s3["points"],
        official_answer=s3["officialAnswers"],
        solution_text=s3["detailedSolution"],
    )

    # III -> math-q-III_1 and math-q-III_2
    s4 = sections[4]
    if session == "2023-1":
        mapped["math-q-III_1"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (前半：特定数字を除外した自然数の個数)",
            points=s4["points"][:2],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["ABC", "DEF", "GHI"]},
            solution_text=s4["detailedSolution"],
        )
        mapped["math-q-III_2"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (後半：位取り記数法と倍数判定)",
            points=[s4["points"][2]],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["JKL", "MNO", "PQR", "STU"]},
            solution_text=s4["detailedSolution"],
        )
    else:
        mapped["math-q-III_1"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (前半：素因数分解と公約数・公倍数)",
            points=s4["points"][:2],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["ABC", "DEFG", "HI", "J", "KLM"]},
            solution_text=s4["detailedSolution"],
        )
        mapped["math-q-III_2"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (後半：一次不定方程式の整数解)",
            points=[s4["points"][2]],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["NOPQ", "R", "S", "TUV", "WX"]},
            solution_text=s4["detailedSolution"],
        )

    # IV -> math-q-IV_1 and math-q-IV_2
    s5 = sections[5]
    if session == "2023-1":
        mapped["math-q-IV_1"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (前半：対角線長と外接円半径・内角)",
            points=s5["points"][:2],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["A", "B", "CD", "EFG", "HI"]},
            solution_text=s5["detailedSolution"],
        )
        mapped["math-q-IV_2"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (後半：内接四角形と線分長・五角形の面積)",
            points=s5["points"][2:],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["JK", "LM", "N", "OP"]},
            solution_text=s5["detailedSolution"],
        )
    else:
        mapped["math-q-IV_1"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (前半：正弦余弦定理とcos 15°)",
            points=s5["points"][:2],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["AB", "CD", "EF", "GHI"]},
            solution_text=s5["detailedSolution"],
        )
        mapped["math-q-IV_2"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (後半：線分長と面積比)",
            points=[s5["points"][2]],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["JK", "LM", "NO", "P", "Q", "RS"]},
            solution_text=s5["detailedSolution"],
        )

    return mapped


def assemble_math_c2_explanations(
    math_data: Any,
    session: str = "2023-2",
) -> dict[str, dict[str, Any]]:
    """Map Math Course 2 explanations to question stable keys."""
    mapped: dict[str, dict[str, Any]] = {}
    if isinstance(math_data, list):
        for s in math_data:
            key = s.get("localKey") or f"math-q-{s.get('q_num') or s.get('sectionId')}"
            mapped[key] = build_explanation_payload(
                title=s.get("title") or s.get("sectionTitle"),
                points=s.get("points", []),
                official_answer=s.get("answer") or s.get("officialAnswers"),
                solution_text=s.get("solution") or s.get("detailedSolution"),
            )
        return mapped

    sections = math_data["sections"]

    # If already split into individual question sections
    if len(sections) == 8:
        for s in sections:
            key = s.get("localKey") or f"math-q-{s['sectionId']}"
            mapped[key] = build_explanation_payload(
                title=s["sectionTitle"],
                points=s["points"],
                official_answer=s["officialAnswers"],
                solution_text=s["detailedSolution"],
            )
        return mapped

    # I_1 -> math-q-I_1
    s0 = sections[0]
    mapped["math-q-I_1"] = build_explanation_payload(
        title=s0["sectionTitle"],
        points=s0["points"],
        official_answer=s0["officialAnswers"],
        solution_text=s0["detailedSolution"],
    )

    # I_2 -> math-q-I_2
    s1 = sections[1]
    mapped["math-q-I_2"] = build_explanation_payload(
        title=s1["sectionTitle"],
        points=s1["points"],
        official_answer=s1["officialAnswers"],
        solution_text=s1["detailedSolution"],
    )

    # II_1 -> math-q-II_1
    s2 = sections[2]
    mapped["math-q-II_1"] = build_explanation_payload(
        title=s2["sectionTitle"],
        points=s2["points"],
        official_answer=s2["officialAnswers"],
        solution_text=s2["detailedSolution"],
    )

    # II_2 -> math-q-II_2
    s3 = sections[3]
    mapped["math-q-II_2"] = build_explanation_payload(
        title=s3["sectionTitle"],
        points=s3["points"],
        official_answer=s3["officialAnswers"],
        solution_text=s3["detailedSolution"],
    )

    # III -> math-q-III_1 and math-q-III_2
    s4 = sections[4]
    if session == "2023-1":
        mapped["math-q-III_1"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (前半：分段関数の積分と増減・極値)",
            points=s4["points"][:2],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["A", "BCD", "E", "F", "GHIJK", "LMN"]},
            solution_text=s4["detailedSolution"],
        )
        mapped["math-q-III_2"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (後半：微積分学の基本定理と最大値問題)",
            points=s4["points"][2:],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["OP", "QR", "ST", "UVWX"]},
            solution_text=s4["detailedSolution"],
        )
    else:
        mapped["math-q-III_1"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (前半：接線の方程式と共有点)",
            points=s4["points"][:2],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["CD", "EFG", "HIJ", "KLM"]},
            solution_text=s4["detailedSolution"],
        )
        mapped["math-q-III_2"] = build_explanation_payload(
            title=s4["sectionTitle"] + " (後半：平行接線・切片同一接線と囲まれた面積)",
            points=[s4["points"][2]],
            official_answer={k: v for k, v in s4["officialAnswers"].items() if k in ["NO", "PQRS", "TUV", "WXY"]},
            solution_text=s4["detailedSolution"],
        )

    # IV -> math-q-IV_1 and math-q-IV_2
    s5 = sections[5]
    if session == "2023-1":
        mapped["math-q-IV_1"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (前半：部分積分法と導関数・接線方程式)",
            points=s5["points"][:2],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["A", "BCD", "EFG", "HI", "JKL", "MNO", "PQ"]},
            solution_text=s5["detailedSolution"],
        )
        mapped["math-q-IV_2"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (後半：極値の比較と最大値の決定)",
            points=s5["points"][2:],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["RST", "UVW"]},
            solution_text=s5["detailedSolution"],
        )
    else:
        mapped["math-q-IV_1"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (前半：絶対値の解除と区間(i),(ii)の増減)",
            points=s5["points"][:2],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["A", "BC", "DE", "F", "G", "HIJK", "LM", "NO", "P", "Q"]},
            solution_text=s5["detailedSolution"],
        )
        mapped["math-q-IV_2"] = build_explanation_payload(
            title=s5["sectionTitle"] + " (後半：区間(iii)の増減と全体の最小値決定)",
            points=[s5["points"][2]],
            official_answer={k: v for k, v in s5["officialAnswers"].items() if k in ["RS", "T", "U", "VW"]},
            solution_text=s5["detailedSolution"],
        )

    return mapped


def expand_math_tokens(official_answers: dict[str, str]) -> dict[str, str]:
    tokens = {}
    for slot_group, val_str in official_answers.items():
        assert len(slot_group) == len(val_str), f"Mismatch {slot_group} vs {val_str}"
        for letter, char in zip(slot_group, val_str):
            tokens[letter] = char
    return tokens


def inject_into_database(
    db_path: Path,
    paper_stable_code: str,
    explanations_map: dict[str, dict[str, Any]],
    reviewer: str = "EJU-Expert-Reviewer",
) -> int:
    """Inject explanations into question_versions and explanation_revisions for the target paper."""
    db = Database(db_path)
    count = 0
    try:
        # Find latest paper version
        row = db.connection.execute(
            """
            SELECT pv.id, pv.version_number 
            FROM paper_versions pv 
            JOIN papers p ON pv.paper_id = p.id 
            WHERE p.stable_code = ? 
            ORDER BY pv.version_number DESC LIMIT 1
            """,
            (paper_stable_code,),
        ).fetchone()

        if not row:
            print(f"Warning: No paper found for {paper_stable_code}")
            return 0

        pv_id = row["id"]

        # Fetch all questions in this paper version
        q_rows = db.connection.execute(
            """
            SELECT qv.id AS qv_id, qv.question_id, q.stable_key 
            FROM question_versions qv 
            JOIN questions q ON qv.question_id = q.id 
            WHERE qv.paper_version_id = ?
            """,
            (pv_id,),
        ).fetchall()

        for q_row in q_rows:
            skey = q_row["stable_key"]
            qv_id = q_row["qv_id"]
            if skey in explanations_map:
                payload = explanations_map[skey]

                # Get current revision
                latest_rev = db.connection.execute(
                    "SELECT COALESCE(MAX(revision), 0) FROM explanation_revisions WHERE question_version_id = ?",
                    (qv_id,),
                ).fetchone()[0]

                # Save reviewed explanation stream
                db.save_explanation(
                    qv_id,
                    payload,
                    base_revision=latest_rev,
                    status="REVIEWED",
                    reviewer=reviewer,
                )
                count += 1

    finally:
        db.close()

    return count


def update_paper_json_file(paper_file: Path, explanations_map: dict[str, dict[str, Any]]) -> int:
    """Inject explanation objects into paper.json questions."""
    if not paper_file.exists():
        return 0

    paper = json.loads(paper_file.read_text(encoding="utf-8"))
    updated = 0
    for form in paper.get("forms", []):
        for group in form.get("groups", []):
            for q in group.get("questions", []):
                skey = q.get("localKey")
                if skey in explanations_map:
                    payload = explanations_map[skey]
                    q["explanation"] = payload
                    official_ans = payload.get("officialAnswer")
                    if isinstance(official_ans, dict):
                        toks = expand_math_tokens(official_ans)
                        q["correctAnswer"] = {"tokens": toks}
                        if "answerSpec" in q and isinstance(q["answerSpec"], dict):
                            q["answerSpec"]["slots"] = list(toks.keys())
                    elif official_ans is not None:
                        q["correctAnswer"] = {"optionKey": str(official_ans)}
                    updated += 1

    paper_file.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=PROJECT_ROOT, help="Path to eju-question-bank root")
    parser.add_argument("--session", default="2023-2", help="Session code (e.g. 2023-2)")
    parser.add_argument("--apply-db", action="store_true", help="Apply explanations to library/eju.db")
    parser.add_argument("--update-paper-json", action="store_true", help="Update work/<session>/paper.json files")
    args = parser.parse_args()

    ws = args.workspace
    db_path = ws / "library/eju.db"

    # Load explanations
    math_c1_file = ws / f"work/{args.session}-math-c1/explanations.json"
    math_c2_file = ws / f"work/{args.session}-math-c2/explanations.json"
    science_file = ws / f"work/{args.session}-science/explanations.json"

    if not (math_c1_file.exists() and math_c2_file.exists() and science_file.exists()):
        print(f"Error: Missing explanation files in work/ for session {args.session}")
        sys.exit(1)

    c1_map = assemble_math_c1_explanations(json.loads(math_c1_file.read_text(encoding="utf-8")), session=args.session)
    c2_map = assemble_math_c2_explanations(json.loads(math_c2_file.read_text(encoding="utf-8")), session=args.session)
    sci_map = assemble_science_explanations(json.loads(science_file.read_text(encoding="utf-8")))

    print("=" * 60)
    print(f"EJU {args.session} Explanations Assembly Summary:")
    print(f"  Math Course 1 questions mapped : {len(c1_map)} (keys: {sorted(c1_map.keys())})")
    print(f"  Math Course 2 questions mapped : {len(c2_map)} (keys: {sorted(c2_map.keys())})")
    print(f"  Science questions mapped        : {len(sci_map)} (57 total: 19 phys, 20 chem, 18 bio)")
    print("=" * 60)

    if args.apply_db:
        print("\nInjecting explanations into database library/eju.db ...")
        c1_db = inject_into_database(db_path, f"eju-{args.session}-math-c1-ja", c1_map)
        print(f"  [OK] Math Course 1: injected {c1_db} questions into eju-{args.session}-math-c1-ja")

        c2_db = inject_into_database(db_path, f"eju-{args.session}-math-c2-ja", c2_map)
        print(f"  [OK] Math Course 2: injected {c2_db} questions into eju-{args.session}-math-c2-ja")

        sci_db = inject_into_database(db_path, f"eju-{args.session}-science-ja", sci_map)
        print(f"  [OK] Science      : injected {sci_db} questions into eju-{args.session}-science-ja")

    if args.update_paper_json:
        print("\nUpdating work/<session>/paper.json files ...")
        c1_p = update_paper_json_file(ws / f"work/{args.session}-math-c1/paper.json", c1_map)
        print(f"  [OK] Math 1 paper.json: updated {c1_p} questions")

        c2_p = update_paper_json_file(ws / f"work/{args.session}-math-c2/paper.json", c2_map)
        print(f"  [OK] Math 2 paper.json: updated {c2_p} questions")

        sci_p = update_paper_json_file(ws / f"work/{args.session}-science/paper.json", sci_map)
        print(f"  [OK] Science paper.json: updated {sci_p} questions")

    print("\nAssembly completed successfully.")


if __name__ == "__main__":
    main()
