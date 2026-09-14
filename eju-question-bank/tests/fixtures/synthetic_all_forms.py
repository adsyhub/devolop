"""Synthetic fixture generator covering all 13 EJU form codes with zero copyright dependency."""

from __future__ import annotations

import copy
from typing import Any
from eju_bank.constants import FORM_SPECS
from eju_bank.util import stable_id, digest_json

def create_synthetic_paper() -> dict[str, Any]:
    source_id = "src_synthetic_fixture_001"
    forms = []

    # 1. JAPANESE_JA: WRITING (essay), READING (choice), LISTENING (audio-linked choice)
    forms.append({
        "formCode": "JAPANESE_JA",
        "spec": FORM_SPECS["JAPANESE_JA"].to_dict(),
        "groups": [
            {
                "groupId": stable_id("g_", source_id, "JAPANESE_JA", "WRITING"),
                "groupCode": "WRITING",
                "materials": [
                    {
                        "materialId": stable_id("m_", source_id, "JAPANESE_JA", "WRITING", "prompt-m1"),
                        "localKey": "writing-prompt-m1",
                        "contentAst": [
                            {"type": "text", "value": "科学技術の発展と環境保護のバランスについて、あなたの考えを述べなさい。"},
                            {"type": "paragraph", "value": "（400字～500字程度で書きなさい）"}
                        ],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 1, "bbox": [0.1, 0.1, 0.9, 0.3]}]
                    }
                ],
                "questions": [
                    {
                        "questionId": stable_id("q_", source_id, "JAPANESE_JA", "q-essay"),
                        "localKey": "q-essay",
                        "sequence": 1,
                        "printedLabel": "記述問題",
                        "sectionCode": "WRITING",
                        "answerRef": None,
                        "stemAst": [
                            {"type": "text", "value": "提示されたテーマについて理由を挙げて論述しなさい。"}
                        ],
                        "options": [],
                        "answerSpec": {
                            "type": "ESSAY",
                            "rubricId": "rubric_japanese_writing_standard"
                        },
                        "correctAnswer": None,
                        "materialRefs": ["writing-prompt-m1"],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 1, "bbox": [0.1, 0.3, 0.9, 0.5]}]
                    }
                ]
            },
            {
                "groupId": stable_id("g_", source_id, "JAPANESE_JA", "READING"),
                "groupCode": "READING",
                "materials": [
                    {
                        "materialId": stable_id("m_", source_id, "JAPANESE_JA", "READING", "reading-m1"),
                        "localKey": "reading-m1",
                        "contentAst": [
                            {"type": "text", "value": "近代化とともに都市の景観は大きく変化した。古くからの"},
                            {"type": "ruby", "base": "町並み", "ruby": "まちなみ"},
                            {"type": "text", "value": "を守る動きも各地で見られる。"}
                        ],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 2, "bbox": [0.1, 0.1, 0.9, 0.4]}]
                    }
                ],
                "questions": [
                    {
                        "questionId": stable_id("q_", source_id, "JAPANESE_JA", "q-reading-1"),
                        "localKey": "q-reading-1",
                        "sequence": 2,
                        "printedLabel": "問1",
                        "sectionCode": "READING",
                        "answerRef": "JA:R:1",
                        "stemAst": [
                            {"type": "text", "value": "筆者が最も主張したいことは何か。"}
                        ],
                        "options": [
                            {"key": "1", "contentAst": [{"type": "text", "value": "伝統的町並みの保存が最優先である。"}]},
                            {"key": "2", "contentAst": [{"type": "text", "value": "都市の変化は避けられない。"}]},
                            {"key": "3", "contentAst": [{"type": "text", "value": "保存と発展の調和が重要である。"}]},
                            {"key": "4", "contentAst": [{"type": "text", "value": "新しい景観こそが望ましい。"}]}
                        ],
                        "answerSpec": {"type": "SINGLE_CHOICE"},
                        "correctAnswer": {"optionKey": "3"},
                        "materialRefs": ["reading-m1"],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 2, "bbox": [0.1, 0.4, 0.9, 0.7]}]
                    }
                ]
            },
            {
                "groupId": stable_id("g_", source_id, "JAPANESE_JA", "LISTENING"),
                "groupCode": "LISTENING",
                "materials": [
                    {
                        "materialId": stable_id("m_", source_id, "JAPANESE_JA", "LISTENING", "listening-m1"),
                        "localKey": "listening-m1",
                        "contentAst": [
                            {"type": "figure", "assetId": 'd1d93d54f956293ce9732d011a038f318e2bee15b81ce686dc0e9b5c3996f913', "sourceBbox": [0.2, 0.2, 0.8, 0.5]}
                        ],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 3, "bbox": [0.1, 0.1, 0.9, 0.5]}]
                    }
                ],
                "questions": [
                    {
                        "questionId": stable_id("q_", source_id, "JAPANESE_JA", "q-listening-1"),
                        "localKey": "q-listening-1",
                        "sequence": 3,
                        "printedLabel": "問1",
                        "sectionCode": "LISTENING_READING_AND_LISTENING",
                        "answerRef": "JA:L:1",
                        "stemAst": [
                            {"type": "text", "value": "音声を聞いて、図の中のどの位置について話しているか選びなさい。"}
                        ],
                        "options": [
                            {"key": "1", "contentAst": [{"type": "text", "value": "地点A"}]},
                            {"key": "2", "contentAst": [{"type": "text", "value": "地点B"}]},
                            {"key": "3", "contentAst": [{"type": "text", "value": "地点C"}]},
                            {"key": "4", "contentAst": [{"type": "text", "value": "地点D"}]}
                        ],
                        "answerSpec": {"type": "SINGLE_CHOICE"},
                        "correctAnswer": {"optionKey": "2"},
                        "materialRefs": ["listening-m1"],
                        "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 3, "bbox": [0.1, 0.5, 0.9, 0.8]}]
                    }
                ]
            }
        ]
    })

    # Science subjects helper
    def _make_choice_question(form_code: str, num: int, stem_text: str, options_list: list[str], correct_key: str, *, figure: bool = False, math_latex: str = None) -> dict:
        stem_ast = [{"type": "text", "value": stem_text}]
        if math_latex:
            stem_ast.append({"type": "inlineMath", "latex": math_latex})
        if figure:
            stem_ast.append({"type": "figure", "assetId": 'd1d93d54f956293ce9732d011a038f318e2bee15b81ce686dc0e9b5c3996f913', "sourceBbox": [0.2, 0.2, 0.8, 0.5]})
        return {
            "questionId": stable_id("q_", source_id, form_code, f"q{num}"),
            "localKey": f"q{num}",
            "printedLabel": f"問{num}",
            "sectionCode": "MAIN",
            "answerRef": f"{form_code.split('_')[0]}:{num}",
            "stemAst": stem_ast,
            "options": [{"key": str(i+1), "contentAst": [{"type": "text", "value": opt}]} for i, opt in enumerate(options_list)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": {"optionKey": correct_key},
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 4 + num, "bbox": [0.1, 0.1, 0.9, 0.8]}]
        }

    # Helper for digit grid question
    def _make_grid_question(form_code: str, num: int, stem_text: str, slots: list[str], tokens: dict[str, str], math_latex: str = None) -> dict:
        stem_ast = [{"type": "text", "value": stem_text}]
        if math_latex:
            stem_ast.append({"type": "displayMath", "latex": math_latex})
        return {
            "questionId": stable_id("q_", source_id, form_code, f"q{num}"),
            "localKey": f"q{num}",
            "printedLabel": f"問{num}",
            "sectionCode": "MAIN",
            "answerRef": f"{form_code.split('_')[0]}:{num}",
            "stemAst": stem_ast,
            "options": [],
            "answerSpec": {"type": "DIGIT_GRID", "slots": slots, "allowedTokens": ["-"] + [str(i) for i in range(10)]},
            "correctAnswer": {"tokens": tokens},
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 10 + num, "bbox": [0.1, 0.1, 0.9, 0.8]}]
        }

    # 2. PHYSICS_JA
    forms.append({
        "formCode": "PHYSICS_JA",
        "spec": FORM_SPECS["PHYSICS_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "PHYSICS_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("PHYSICS_JA", 1, "初速度v0で投げ上げられた小球の最高点での速度はいくつか。", ["0 m/s", "v0/2", "v0", "2v0"], "1", figure=True, math_latex="v_0")]
        }]
    })

    # 3. PHYSICS_EN
    forms.append({
        "formCode": "PHYSICS_EN",
        "spec": FORM_SPECS["PHYSICS_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "PHYSICS_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("PHYSICS_EN", 1, "What is the acceleration due to gravity on Earth near the surface?", ["4.9 m/s^2", "9.8 m/s^2", "19.6 m/s^2", "32 m/s^2"], "2", math_latex="g \\approx 9.8 \\text{ m/s}^2")]
        }]
    })

    # 4. CHEMISTRY_JA
    forms.append({
        "formCode": "CHEMISTRY_JA",
        "spec": FORM_SPECS["CHEMISTRY_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "CHEMISTRY_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("CHEMISTRY_JA", 1, "次の気体のうち、水に極めて溶けやすいものはどれか。", ["水素", "アンモニア", "酸素", "窒素"], "2", math_latex="\\text{NH}_3")]
        }]
    })

    # 5. CHEMISTRY_EN
    forms.append({
        "formCode": "CHEMISTRY_EN",
        "spec": FORM_SPECS["CHEMISTRY_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "CHEMISTRY_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("CHEMISTRY_EN", 1, "Which of the following compounds has ionic bonding?", ["CH4", "NaCl", "CO2", "H2O"], "2", math_latex="\\text{NaCl}")]
        }]
    })

    # 6. BIOLOGY_JA
    forms.append({
        "formCode": "BIOLOGY_JA",
        "spec": FORM_SPECS["BIOLOGY_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "BIOLOGY_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("BIOLOGY_JA", 1, "ATPの合成を主に行う細胞小器官はどれか。", ["リボソーム", "ゴルジ体", "ミトコンドリア", "小胞体"], "3")]
        }]
    })

    # 7. BIOLOGY_EN
    forms.append({
        "formCode": "BIOLOGY_EN",
        "spec": FORM_SPECS["BIOLOGY_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "BIOLOGY_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("BIOLOGY_EN", 1, "Which organelle is responsible for cellular respiration in eukaryotic cells?", ["Chloroplast", "Mitochondria", "Nucleus", "Vacuole"], "2")]
        }]
    })

    # 8. JAPAN_AND_WORLD_JA
    forms.append({
        "formCode": "JAPAN_AND_WORLD_JA",
        "spec": FORM_SPECS["JAPAN_AND_WORLD_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "JAPAN_AND_WORLD_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("JAPAN_AND_WORLD_JA", 1, "日本国憲法における三大原理に含まれないものはどれか。", ["国民主権", "基本的人権の尊重", "平和主義", "大統領制"], "4")]
        }]
    })

    # 9. JAPAN_AND_WORLD_EN
    forms.append({
        "formCode": "JAPAN_AND_WORLD_EN",
        "spec": FORM_SPECS["JAPAN_AND_WORLD_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "JAPAN_AND_WORLD_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_choice_question("JAPAN_AND_WORLD_EN", 1, "Which international organization was founded in 1945 to maintain international peace and security?", ["League of Nations", "United Nations", "WTO", "IMF"], "2")]
        }]
    })

    # 10. MATHEMATICS_COURSE_1_JA
    forms.append({
        "formCode": "MATHEMATICS_COURSE_1_JA",
        "spec": FORM_SPECS["MATHEMATICS_COURSE_1_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "MATHEMATICS_COURSE_1_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_grid_question(
                "MATHEMATICS_COURSE_1_JA", 1,
                "2次関数 y = x^2 - 4x + 1 の頂点の座標を求めなさい。( [A], [B][C] )",
                ["A", "B", "C"],
                {"A": "2", "B": "-", "C": "3"},
                math_latex="y = (x - 2)^2 - 3"
            )]
        }]
    })

    # 11. MATHEMATICS_COURSE_1_EN
    forms.append({
        "formCode": "MATHEMATICS_COURSE_1_EN",
        "spec": FORM_SPECS["MATHEMATICS_COURSE_1_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "MATHEMATICS_COURSE_1_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_grid_question(
                "MATHEMATICS_COURSE_1_EN", 1,
                "Find the vertex of parabola y = x^2 - 6x + 5: ( [A], [B][C] )",
                ["A", "B", "C"],
                {"A": "3", "B": "-", "C": "4"},
                math_latex="y = (x - 3)^2 - 4"
            )]
        }]
    })

    # 12. MATHEMATICS_COURSE_2_JA
    forms.append({
        "formCode": "MATHEMATICS_COURSE_2_JA",
        "spec": FORM_SPECS["MATHEMATICS_COURSE_2_JA"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "MATHEMATICS_COURSE_2_JA", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_grid_question(
                "MATHEMATICS_COURSE_2_JA", 1,
                "関数 f(x) = x^3 - 3x の極大値を [A] とし、極小値を [B][C] とする。",
                ["A", "B", "C"],
                {"A": "2", "B": "-", "C": "2"},
                math_latex="f'(x) = 3x^2 - 3 = 0 \\implies x = \\pm 1"
            )]
        }]
    })

    # 13. MATHEMATICS_COURSE_2_EN
    forms.append({
        "formCode": "MATHEMATICS_COURSE_2_EN",
        "spec": FORM_SPECS["MATHEMATICS_COURSE_2_EN"].to_dict(),
        "groups": [{
            "groupId": stable_id("g_", source_id, "MATHEMATICS_COURSE_2_EN", "I"),
            "groupCode": "I",
            "materials": [],
            "questions": [_make_grid_question(
                "MATHEMATICS_COURSE_2_EN", 1,
                "Compute the definite integral: \\int_0^2 (3x^2 - 2x) dx = [A]",
                ["A"],
                {"A": "4"},
                math_latex="[x^3 - x^2]_0^2 = 8 - 4 = 4"
            )]
        }]
    })

    paper = {
        "schemaVersion": 1,
        "examFamily": "EJU",
        "paperId": stable_id("p_", "eju-synthetic-all-13-forms"),
        "stableCode": "eju-synthetic-all-13-forms",
        "title": "EJU Synthetic Full Suite (All 13 Forms)",
        "session": "2024-SYNTH",
        "syllabusVersion": "2015",
        "contentKind": "SYNTHETIC",
        "completeness": "COMPLETE",
        "availableModes": ["PRACTICE", "SECTION", "MOCK"],
        "source": {
            "sourceId": source_id,
            "rights": {
                "status": "PUBLIC_LICENSED",
                "note": "Synthetic test fixture created for automated compliance testing."
            },
            "files": [
                {
                    "role": "QUESTION_BOOKLET",
                    "path": "synthetic-questions.pdf",
                    "fileName": "synthetic-questions.pdf",
                    "sizeBytes": 1024,
                    "sha256": "0" * 64
                }
            ]
        },
        "forms": forms,
        "questionCount": 15
    }

    # Sequence numbering
    seq = 0
    for form in paper["forms"]:
        for group in form["groups"]:
            for question in group["questions"]:
                seq += 1
                question["sequence"] = seq
    paper["questionCount"] = seq

    rev_dict = copy.deepcopy(paper)
    rev_dict.pop("contentRevision", None)
    paper["contentRevision"] = digest_json(rev_dict)
    return paper

if __name__ == "__main__":
    import json
    paper = create_synthetic_paper()
    with open("/workspace/Develop/eju-question-bank/tests/fixtures/synthetic_paper.json", "w", encoding="utf-8") as f:
        json.dump(paper, f, ensure_ascii=False, indent=2)
    print(f"Synthetic paper with {len(paper['forms'])} forms and {paper['questionCount']} questions generated.")
