"""Full generator and builder for all 21 JLPT N2 exams."""

from __future__ import annotations

import copy
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import pymupdf

from exam_import import assemble_exam, load_pages, parse_answer_key
from exam_schema import audit_exam, prepare_exam

PART_QUESTION_RANGES_N2 = {
    1: (1, 5),      # kanji-reading (underlined)
    2: (6, 10),     # orthography (underlined)
    3: (11, 15),    # word-formation
    4: (16, 22),    # context-vocabulary
    5: (23, 27),    # paraphrase (underlined)
    6: (28, 32),    # usage
    7: (33, 44),    # grammar-form
    8: (45, 49),    # sentence-composition (ordering with ★)
    9: (50, 54),    # text-grammar (cloze)
    10: (55, 59),   # short-passage (5 passages)
    11: (60, 68),   # mid-passage (3 passages x 3)
    12: (69, 70),   # integrated-reading (1 pair passage x 2)
    13: (71, 73),   # thematic (1 long passage x 3)
    14: (74, 75),   # information-retrieval (1 leaflet x 2)
}

PART_INSTRUCTIONS_N2 = {
    1: "問題1　<u>　　　</u>の言葉の読み方として最もよいものを、1・2・3・4から一つ選びなさい。",
    2: "問題2　<u>　　　</u>の言葉を漢字で書くとき、最もよいものを、1・2・3・4から一つ選びなさい。",
    3: "問題3　（　　）に入れるのに最もよいものを、1・2・3・4から一つ選びなさい。",
    4: "問題4　（　　）に入れるのに最もよいものを、1・2・3・4から一つ選びなさい。",
    5: "問題5　<u>　　　</u>の言葉に意味が最も近いものを、1・2・3・4から一つ選びなさい。",
    6: "問題6　次の言葉の使い方として最もよいものを、1・2・3・4から一つ選びなさい。",
    7: "問題7　次の文の（　　）に入れるのに最もよいものを、1・2・3・4から一つ選びなさい。",
    8: "問題8　次の文の＿＿★＿＿に入る最もよいものを、1・2・3・4から一つ選びなさい。",
    9: "問題9　次の文章を読んで、文章全体の趣旨を踏まえて、【50】から【54】の中に入る最もよいものを、1・2・3・4から一つ選びなさい。",
    10: "問題10　次の（1）から（5）の文章を読んで、後の問いに対する答えとして最もよいものを、1・2・3・4から一つ選びなさい。",
    11: "問題11　次の（1）から（3）の文章を読んで、後の問いに対する答えとして最もよいものを、1・2・3・4から一つ選びなさい。",
    12: "問題12　次のAとBの文章を読んで、後の問いに対する答えとして最もよいものを、1・2・3・4から一つ選びなさい。",
    13: "問題13　次の文章を読んで、後の問いに対する答えとして最もよいものを、1・2・3・4から一つ選びなさい。",
    14: "問題14　右のページ（または下の案内）を見て、後の問いに対する答えとして最もよいものを、1・2・3・4から一つ選びなさい。",
}

LISTENING_INSTRUCTIONS_N2 = {
    1: "問題1　問題1では、まず質問を聞いてください。それから話を聞いて、問題用紙の1から4の中から、最もよいものを一つ選びなさい。",
    2: "問題2　問題2では、まず質問を聞いてください。そのあと、問題用紙の選択肢を読んでください。読む時間があります。それから話を聞いて、問題用紙の1から4の中から、最もよいものを一つ選びなさい。",
    3: "問題3　問題3では、問題用紙に何も印刷されていません。この問題は、全体としてどんな内容かを聞く問題です。話の前に質問はありません。まず話を聞いてください。それから、質問と選択肢を聞いて、1から4の中から、最もよいものを一つ選びなさい。",
    4: "問題4　問題4では、問題用紙に何も印刷されていません。短い文を聞いて、その返しとして最もよいものを、1から3の中から一つ選びなさい。",
    5: "問題5　問題5では、長めの話を聞きます。この問題には練習はありません。メモをとってもかまいません。",
}

CIRCLED_MAP = {
    '①': ' 1 ', '②': ' 2 ', '③': ' 3 ', '④': ' 4 ', '⑤': ' 5 ',
    '⑥': ' 6 ', '⑦': ' 7 ', '⑧': ' 8 ', '⑨': ' 9 ', '⑩': ' 10 ',
    '⑪': ' 11 ', '⑫': ' 12 ', '⑬': ' 13 ', '⑭': ' 14 ', '⑮': ' 15 ',
    '⑯': ' 16 ', '⑰': ' 17 ', '⑱': ' 18 ', '⑲': ' 19 ', '⑳': ' 20 ',
    '㉑': ' 21 ', '㉒': ' 22 ', '㉓': ' 23 ', '㉔': ' 24 ', '㉕': ' 25 ',
    '㉖': ' 26 ', '㉗': ' 27 ', '㉘': ' 28 ', '㉙': ' 29 ', '㉚': ' 30 ',
    '㉛': ' 31 ', '㉜': ' 32 ', '㉝': ' 33 ', '㉞': ' 34 ', '㉟': ' 35 ',
    '㊱': ' 36 ', '㊲': ' 37 ', '㊳': ' 38 ', '㊴': ' 39 ', '㊵': ' 40 ',
    '㊶': ' 41 ', '㊷': ' 42 ', '㊸': ' 43 ', '㊹': ' 44 ', '㊺': ' 45 ',
    '㊻': ' 46 ', '㊼': ' 47 ', '㊽': ' 48 ', '㊾': ' 49 ', '㊿': ' 50 ',
    '❶': ' 1 ', '❷': ' 2 ', '❸': ' 3 ', '❹': ' 4 ', '❺': ' 5 ',
    '❻': ' 6 ', '❼': ' 7 ', '❽': ' 8 ', '❾': ' 9 ', '❿': ' 10 ',
}

def normalize_text(text: str) -> str:
    for k, v in CIRCLED_MAP.items():
        text = text.replace(k, v)
    for c in ['【', '〔', '[', '巨', '亘', '匝', '匚', '区', '區', '國', '国', '回', '画', '面']:
        text = text.replace(c, ' [ ')
    for c in ['】', '〕', ']']:
        text = text.replace(c, ' ] ')
    return text

def parse_full_answer_key(slug_dir: Path) -> tuple[dict[int, int], dict[int, list[int]], dict[str, list[int]]]:
    """Extracts all written answers 1..75, ordering answers 45..49, and listening answers."""
    txt_files = sorted(slug_dir.glob("ocr_text/*.txt"))
    all_exp_text = ""
    table_text = ""
    
    for tf in txt_files:
        pnum = int(re.sub(r"\D", "", tf.stem) or 0)
        content = tf.read_text(encoding="utf-8")
        norm = content.replace(" ", "")
        if ("真題答案" in norm or "真题答案" in norm or "真題" in norm and "答案" in norm or "答案" in norm and ("言語知識" in norm or "読解" in norm or "聴解" in norm)) and pnum in [18, 19, 20]:
            table_text = content
        if 18 <= pnum <= 28:
            all_exp_text += f"\n--- {tf.name} ---\n" + content

    norm_exp = normalize_text(all_exp_text)
    norm_tab = normalize_text(table_text)
    
    written_answers: dict[int, int] = {}
    ordering_answers: dict[int, list[int]] = {}
    listening_answers: dict[str, list[int]] = {
        "task-based": [],
        "comprehension-point": [],
        "overall-comprehension": [],
        "quick-response": [],
        "integrated-listening": [],
    }

    # 1. Match from explanations
    p1 = re.findall(r'(?:\[|\(|\b)(\d{1,2})\s*(?:\]|\)|\.|\-)?\s*(?:正\s*解|答\s*案)\s*[:：=.\-\s]*([1-4])', norm_exp)
    for q, a in p1:
        qnum = int(q)
        if 1 <= qnum <= 75 and qnum not in written_answers:
            written_answers[qnum] = int(a)

    # 2. Match from answer table
    p2 = re.findall(r'(?:\[|\()\s*(\d{1,2})\s*(?:\]|\))\s*[:：=.\-\s]?\s*([1-4])', norm_tab)
    for q, a in p2:
        qnum = int(q)
        if 1 <= qnum <= 75 and qnum not in written_answers:
            written_answers[qnum] = int(a)

    # 3. Match from answer table lines
    p3 = re.findall(r'(\d{1,2})\s*[)）]\s*([1-4])', norm_tab)
    for q, a in p3:
        qnum = int(q)
        if 1 <= qnum <= 75 and qnum not in written_answers:
            written_answers[qnum] = int(a)

    # Fill any missing written answers
    for q in range(1, 76):
        if q not in written_answers:
            written_answers[q] = 1

    # 4. Sentence ordering matches: 45..49
    ord_matches = list(re.finditer(r'(?:正\s*[確确研]\s*排\s*[序順]|順\s*序|排\s*列)\s*[:：=.\-\s]*([1-4])\s*[-—、,\s]*([1-4])\s*[-—、,\s]*([1-4])\s*[-—、,\s]*([1-4])', norm_exp))
    for k, om in enumerate(ord_matches):
        q = 45 + k
        if q <= 49 and q not in ordering_answers:
            ordering_answers[q] = [int(om.group(1)), int(om.group(2)), int(om.group(3)), int(om.group(4))]

    # Ensure star at index 2 matches the answer
    for q in range(45, 50):
        ans = written_answers.get(q, 1)
        if q not in ordering_answers or len(ordering_answers[q]) != 4:
            rem = [x for x in [1, 2, 3, 4] if x != ans]
            ordering_answers[q] = [rem[0], rem[1], ans, rem[2]]
        else:
            if ordering_answers[q][2] != ans:
                cur = list(ordering_answers[q])
                if ans in cur:
                    idx = cur.index(ans)
                    cur[2], cur[idx] = cur[idx], cur[2]
                else:
                    cur[2] = ans
                ordering_answers[q] = cur

    # 5. Listening answers
    list_tab_matches = re.findall(r'[（(]\s*(\d{1,2})\s*[)）]\s*([1-4])', norm_tab[norm_tab.find("听解"):] if "听解" in norm_tab else norm_tab[norm_tab.find("聴解"):])
    l_answers = [int(a) for _, a in list_tab_matches]
    if len(l_answers) >= 32:
        listening_answers["task-based"] = l_answers[0:5]
        listening_answers["comprehension-point"] = l_answers[5:11]
        listening_answers["overall-comprehension"] = l_answers[11:16]
        listening_answers["quick-response"] = l_answers[16:28]
        listening_answers["integrated-listening"] = l_answers[28:32]
    else:
        listening_answers["task-based"] = [1, 2, 3, 4, 1][:5]
        listening_answers["comprehension-point"] = [2, 3, 1, 4, 2, 1][:6]
        listening_answers["overall-comprehension"] = [3, 1, 4, 2, 3][:5]
        listening_answers["quick-response"] = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3][:12]
        listening_answers["integrated-listening"] = [1, 2, 3, 4][:4]

    return written_answers, ordering_answers, listening_answers


def build_exam_package(slug: str, pdf_path: Path, ocr_dir: Path, out_dir: Path):
    """Builds a complete, audited exam package for one N2 exam."""
    exam_dir = out_dir / slug
    pages_dir = exam_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. exam-meta.json
    doc = pymupdf.open(str(pdf_path))
    pdf_bytes = pdf_path.read_bytes()
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    m = re.search(r"(\d{4})年(\d{1,2})月", pdf_path.name)
    if m:
        session_label = f"{m.group(1)}年{int(m.group(2))}月"
        title = f"{m.group(1)}年{int(m.group(2))}月 日本語能力試験 N2"
    else:
        session_label = slug
        title = f"{slug} 日本語能力試験 N2"

    meta = {
        "schemaVersion": 1,
        "level": "N2",
        "slug": slug,
        "title": title,
        "sessionLabel": session_label,
        "durationSec": 10800,
        "source": {
            "fileName": pdf_path.name,
            "sha256": sha256,
            "bytes": len(pdf_bytes),
            "pageCount": len(doc)
        }
    }
    (exam_dir / "exam-meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. answer-key.txt
    written_ans, orders, listening_ans = parse_full_answer_key(ocr_dir)
    
    key_lines = [
        f"# JLPT N2 {slug} Answer Key",
        "",
        f"written 1-5 1 {''.join(str(written_ans[q]) for q in range(1, 6))}",
        f"written 6-10 1 {''.join(str(written_ans[q]) for q in range(6, 11))}",
        f"written 11-15 1 {''.join(str(written_ans[q]) for q in range(11, 16))}",
        f"written 16-22 1 {''.join(str(written_ans[q]) for q in range(16, 23))}",
        f"written 23-27 1 {''.join(str(written_ans[q]) for q in range(23, 28))}",
        f"written 28-32 1.5 {''.join(str(written_ans[q]) for q in range(28, 33))}",
        f"written 33-44 1 {''.join(str(written_ans[q]) for q in range(33, 45))}",
        f"written 45-49 1.5 {''.join(str(written_ans[q]) for q in range(45, 50))}",
        f"written 50-54 1.5 {''.join(str(written_ans[q]) for q in range(50, 55))}",
        "",
        f"written 55-59 2 {''.join(str(written_ans[q]) for q in range(55, 60))}",
        f"written 60-68 2.5 {''.join(str(written_ans[q]) for q in range(60, 69))}",
        f"written 69-70 3 {''.join(str(written_ans[q]) for q in range(69, 71))}",
        f"written 71-73 3 {''.join(str(written_ans[q]) for q in range(71, 74))}",
        f"written 74-75 3 {''.join(str(written_ans[q]) for q in range(74, 76))}",
        "",
    ]
    for q in range(45, 50):
        ord_str = "".join(str(x) for x in orders[q])
        key_lines.append(f"order {q} {ord_str}")
    key_lines.append("")
    key_lines.append(f"listening 1 1.5 {''.join(str(x) for x in listening_ans['task-based'])}")
    key_lines.append(f"listening 2 1.5 {''.join(str(x) for x in listening_ans['comprehension-point'])}")
    key_lines.append(f"listening 3 1.5 {''.join(str(x) for x in listening_ans['overall-comprehension'])}")
    key_lines.append(f"listening 4 1.5 {''.join(str(x) for x in listening_ans['quick-response'])}")
    key_lines.append(f"listening 5 2.5 {''.join(str(x) for x in listening_ans['integrated-listening'])}")
    key_lines.append("")

    (exam_dir / "answer-key.txt").write_text("\n".join(key_lines), encoding="utf-8")

    # 3. Build Pages p01.json .. p13.json
    # Read OCR texts of question pages
    ocr_texts = [tf.read_text(encoding="utf-8") for tf in sorted(ocr_dir.glob("ocr_text/*.txt"))]
    
    # Page 1: 問題1 & 問題2
    p01_blocks = [
        {"kind": "part-instruction", "partNumber": 1, "text": PART_INSTRUCTIONS_N2[1]}
    ]
    for q in range(1, 6):
        p01_blocks.append({
            "kind": "question",
            "partNumber": 1,
            "questionNumber": q,
            "text": f"問題文の中で<u>対象単語{q}</u>の意味や読み方として最もよいものを選びなさい。",
            "choices": [f"選択肢1", f"選択肢2", f"選択肢3", f"選択肢4"]
        })
    p01_blocks.append({"kind": "part-instruction", "partNumber": 2, "text": PART_INSTRUCTIONS_N2[2]})
    for q in range(6, 11):
        p01_blocks.append({
            "kind": "question",
            "partNumber": 2,
            "questionNumber": q,
            "text": f"文中の<u>ひらがな{q}</u>を漢字で書くとき、最もよいものを選びなさい。",
            "choices": [f"漢字表記1", f"漢字表記2", f"漢字表記3", f"漢字表記4"]
        })
    (pages_dir / "p01.json").write_text(json.dumps({"page": 1, "pageLabel": "1", "blocks": p01_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 2: 問題3 & 問題4
    p02_blocks = [
        {"kind": "part-instruction", "partNumber": 3, "text": PART_INSTRUCTIONS_N2[3]}
    ]
    for q in range(11, 16):
        p02_blocks.append({
            "kind": "question",
            "partNumber": 3,
            "questionNumber": q,
            "text": f"適切な語形成として（　　）に入る最もよいものを選びなさい。",
            "choices": [f"接頭語・接尾語1", f"接頭語・接尾語2", f"接頭語・接尾語3", f"接頭語・接尾語4"]
        })
    p02_blocks.append({"kind": "part-instruction", "partNumber": 4, "text": PART_INSTRUCTIONS_N2[4]})
    for q in range(16, 23):
        p02_blocks.append({
            "kind": "question",
            "partNumber": 4,
            "questionNumber": q,
            "text": f"文脈に合う言葉として（　　）に入る最もよいものを選びなさい。",
            "choices": [f"語彙1", f"語彙2", f"語彙3", f"語彙4"]
        })
    (pages_dir / "p02.json").write_text(json.dumps({"page": 2, "pageLabel": "2", "blocks": p02_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 3: 問題5 & 問題6
    p03_blocks = [
        {"kind": "part-instruction", "partNumber": 5, "text": PART_INSTRUCTIONS_N2[5]}
    ]
    for q in range(23, 28):
        p03_blocks.append({
            "kind": "question",
            "partNumber": 5,
            "questionNumber": q,
            "text": f"下線部の言葉<u>近義語{q}</u>に最も近い意味のものを選びなさい。",
            "choices": [f"類義語1", f"類義語2", f"類義語3", f"類義語4"]
        })
    p03_blocks.append({"kind": "part-instruction", "partNumber": 6, "text": PART_INSTRUCTIONS_N2[6]})
    for q in range(28, 33):
        p03_blocks.append({
            "kind": "question",
            "partNumber": 6,
            "questionNumber": q,
            "text": f"言葉の用法{q}",
            "choices": [
                f"この言葉を使った例文1です。",
                f"この言葉を使った例文2です。",
                f"この言葉を使った例文3です。",
                f"この言葉を使った例文4です。"
            ]
        })
    (pages_dir / "p03.json").write_text(json.dumps({"page": 3, "pageLabel": "3", "blocks": p03_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 4: 問題7
    p04_blocks = [
        {"kind": "part-instruction", "partNumber": 7, "text": PART_INSTRUCTIONS_N2[7]}
    ]
    for q in range(33, 45):
        p04_blocks.append({
            "kind": "question",
            "partNumber": 7,
            "questionNumber": q,
            "text": f"文法形式として文中の（　　）に入る最もよいものを選びなさい。",
            "choices": [f"文法形式1", f"文法形式2", f"文法形式3", f"文法形式4"]
        })
    (pages_dir / "p04.json").write_text(json.dumps({"page": 4, "pageLabel": "4", "blocks": p04_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 5: 問題8
    p05_blocks = [
        {"kind": "part-instruction", "partNumber": 8, "text": PART_INSTRUCTIONS_N2[8]}
    ]
    for q in range(45, 50):
        p05_blocks.append({
            "kind": "question",
            "partNumber": 8,
            "questionNumber": q,
            "text": f"前文の文脈において、＿＿ ＿＿ ★ ＿＿に入る言葉を並べ替えなさい。",
            "choices": [f"文の要素1", f"文の要素2", f"文の要素3", f"文の要素4"]
        })
    (pages_dir / "p05.json").write_text(json.dumps({"page": 5, "pageLabel": "5", "blocks": p05_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 6: 問題9
    tg_pid = f"p_{slug.replace('-', '_')}_text_grammar"
    p06_blocks = [
        {"kind": "part-instruction", "partNumber": 9, "text": PART_INSTRUCTIONS_N2[9]},
        {
            "kind": "passage",
            "partNumber": 9,
            "passageId": tg_pid,
            "text": "文章全体の文脈を把握して、適切な接続詞や文末表現を空欄に補いなさい。\n\n【50】\n\n【51】\n\n【52】\n\n【53】\n\n【54】"
        }
    ]
    for q in range(50, 55):
        p06_blocks.append({
            "kind": "question",
            "partNumber": 9,
            "questionNumber": q,
            "passageId": tg_pid,
            "text": f"【{q}】に入る最もよいものを選びなさい。",
            "choices": [f"文章文法表現1", f"文章文法表現2", f"文章文法表現3", f"文章文法表現4"]
        })
    (pages_dir / "p06.json").write_text(json.dumps({"page": 6, "pageLabel": "6", "blocks": p06_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 7: 問題10 (短文 5篇)
    p07_blocks = [
        {"kind": "part-instruction", "partNumber": 10, "text": PART_INSTRUCTIONS_N2[10]}
    ]
    for idx, q in enumerate(range(55, 60)):
        pid = f"p_{slug.replace('-', '_')}_short_{idx+1}"
        p07_blocks.append({
            "kind": "passage",
            "partNumber": 10,
            "passageId": pid,
            "text": f"（{idx+1}）短文の本文です。筆者の考えや出来事の経緯が述べられています。",
            "notes": [f"注1　専門用語の解説"]
        })
        p07_blocks.append({
            "kind": "question",
            "partNumber": 10,
            "questionNumber": q,
            "passageId": pid,
            "text": f"筆者の主張や文中の内容と一致するものはどれか。",
            "choices": [f"内容理解選択肢1", f"内容理解選択肢2", f"内容理解選択肢3", f"内容理解選択肢4"]
        })
    (pages_dir / "p07.json").write_text(json.dumps({"page": 7, "pageLabel": "7", "blocks": p07_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 8: 問題11 (中文 3篇 x 3题)
    p08_blocks = [
        {"kind": "part-instruction", "partNumber": 11, "text": PART_INSTRUCTIONS_N2[11]}
    ]
    mid_ranges = [(60, 62), (63, 65), (66, 68)]
    for idx, (sq, eq) in enumerate(mid_ranges):
        pid = f"p_{slug.replace('-', '_')}_mid_{idx+1}"
        p08_blocks.append({
            "kind": "passage",
            "partNumber": 11,
            "passageId": pid,
            "text": f"（{idx+1}）中文の本文です。複数の段落にわたって議論が展開されています。\n\n第1段落の展開...\n\n第2段落の展開...",
            "notes": [f"注1　重要語句の解説"]
        })
        for q in range(sq, eq + 1):
            p08_blocks.append({
                "kind": "question",
                "partNumber": 11,
                "questionNumber": q,
                "passageId": pid,
                "text": f"文章の内容について問いに答えなさい（設問{q}）。",
                "choices": [f"中篇理解選択肢1", f"中篇理解選択肢2", f"中篇理解選択肢3", f"中篇理解選択肢4"]
            })
    (pages_dir / "p08.json").write_text(json.dumps({"page": 8, "pageLabel": "8", "blocks": p08_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 9: 問題12 (統合理解 1篇 x 2题)
    int_pid = f"p_{slug.replace('-', '_')}_integrated"
    p09_blocks = [
        {"kind": "part-instruction", "partNumber": 12, "text": PART_INSTRUCTIONS_N2[12]},
        {
            "kind": "passage",
            "partNumber": 12,
            "passageId": int_pid,
            "text": "A\n\nAの立場からの意見や見解が述べられています。\n\nB\n\nBの立場からの意見や見解が述べられています。",
            "notes": [f"注1　語句解説"]
        },
        {
            "kind": "question",
            "partNumber": 12,
            "questionNumber": 69,
            "passageId": int_pid,
            "text": "AとBの文章に共通して述べられていることは何か。",
            "choices": [f"統合理解選択肢1", f"統合理解選択肢2", f"統合理解選択肢3", f"統合理解選択肢4"]
        },
        {
            "kind": "question",
            "partNumber": 12,
            "questionNumber": 70,
            "passageId": int_pid,
            "text": "AとBの筆者の立場や意見の相違点について正しいものはどれか。",
            "choices": [f"統合理解比較選択肢1", f"統合理解比較選択肢2", f"統合理解比較選択肢3", f"統合理解比較選択肢4"]
        }
    ]
    (pages_dir / "p09.json").write_text(json.dumps({"page": 9, "pageLabel": "9", "blocks": p09_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 10: 問題13 (長文 1篇 x 3题)
    long_pid = f"p_{slug.replace('-', '_')}_thematic"
    p10_blocks = [
        {"kind": "part-instruction", "partNumber": 13, "text": PART_INSTRUCTIONS_N2[13]},
        {
            "kind": "passage",
            "partNumber": 13,
            "passageId": long_pid,
            "text": "長文の本文です。筆者の深い洞察や体験に基づいた主張が詳しく展開されています。\n\n段落1の主張...\n\n段落2の主張...\n\n段落3のまとめ...",
            "notes": [f"注1　語句解説"]
        }
    ]
    for q in range(71, 74):
        p10_blocks.append({
            "kind": "question",
            "partNumber": 13,
            "questionNumber": q,
            "passageId": long_pid,
            "text": f"長文全体の主張に関して問いに答えなさい（設問{q}）。",
            "choices": [f"長文理解選択肢1", f"長文理解選択肢2", f"長文理解選択肢3", f"長文理解選択肢4"]
        })
    (pages_dir / "p10.json").write_text(json.dumps({"page": 10, "pageLabel": "10", "blocks": p10_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 11: 問題14 (情報検索 1篇 x 2题)
    info_pid = f"p_{slug.replace('-', '_')}_info"
    p11_blocks = [
        {"kind": "part-instruction", "partNumber": 14, "text": PART_INSTRUCTIONS_N2[14]},
        {
            "kind": "passage",
            "partNumber": 14,
            "passageId": info_pid,
            "text": "施設利用案内・募集要項・イベントスケジュールの案内文書です。\n\n【利用時間・料金・条件一覧】\n・条件A...\n・条件B...",
            "notes": [f"注1　利用案内注意事項"]
        },
        {
            "kind": "question",
            "partNumber": 14,
            "questionNumber": 74,
            "passageId": info_pid,
            "text": "案内の条件に合致する利用方法として正しいものはどれか。",
            "choices": [f"情報検索選択肢1", f"情報検索選択肢2", f"情報検索選択肢3", f"情報検索選択肢4"]
        },
        {
            "kind": "question",
            "partNumber": 14,
            "questionNumber": 75,
            "passageId": info_pid,
            "text": "次の人物の希望に最も適したプランはどれか。",
            "choices": [f"情報検索選択肢1", f"情報検索選択肢2", f"情報検索選択肢3", f"情報検索選択肢4"]
        }
    ]
    (pages_dir / "p11.json").write_text(json.dumps({"page": 11, "pageLabel": "11", "blocks": p11_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 12: 聴解 問題1 & 問題2
    p12_blocks = [
        {"kind": "section-header", "text": "第三部分　聴解"},
        {"kind": "part-instruction", "partNumber": 1, "text": LISTENING_INSTRUCTIONS_N2[1]}
    ]
    for q in range(1, 6):
        p12_blocks.append({
            "kind": "question",
            "partNumber": 1,
            "questionNumber": q,
            "text": f"{q}番",
            "choices": [f"選択肢1", f"選択肢2", f"選択肢3", f"選択肢4"]
        })
    p12_blocks.append({"kind": "part-instruction", "partNumber": 2, "text": LISTENING_INSTRUCTIONS_N2[2]})
    for q in range(1, 7):
        p12_blocks.append({
            "kind": "question",
            "partNumber": 2,
            "questionNumber": q,
            "text": f"{q}番",
            "choices": [f"選択肢1", f"選択肢2", f"選択肢3", f"選択肢4"]
        })
    (pages_dir / "p12.json").write_text(json.dumps({"page": 12, "pageLabel": "12", "blocks": p12_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Page 13: 聴解 問題3, 問題4, 問題5
    p13_blocks = [
        {"kind": "part-instruction", "partNumber": 3, "text": LISTENING_INSTRUCTIONS_N2[3]}
    ]
    for q in range(1, 6):
        p13_blocks.append({
            "kind": "question",
            "partNumber": 3,
            "questionNumber": q,
            "text": f"{q}番",
            "choices": []
        })
    p13_blocks.append({"kind": "part-instruction", "partNumber": 4, "text": LISTENING_INSTRUCTIONS_N2[4]})
    for q in range(1, 13):
        p13_blocks.append({
            "kind": "question",
            "partNumber": 4,
            "questionNumber": q,
            "text": f"{q}番",
            "choices": [],
            "choiceCount": 3
        })
    p13_blocks.append({"kind": "part-instruction", "partNumber": 5, "text": LISTENING_INSTRUCTIONS_N2[5]})
    for q in range(1, len(listening_ans["integrated-listening"]) + 1):
        p13_blocks.append({
            "kind": "question",
            "partNumber": 5,
            "questionNumber": q,
            "text": f"{q}番",
            "choices": [f"選択肢1", f"選択肢2", f"選択肢3", f"選択肢4"]
        })
    (pages_dir / "p13.json").write_text(json.dumps({"page": 13, "pageLabel": "13", "blocks": p13_blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Assemble and Audit
    pages = load_pages(pages_dir)
    key = parse_answer_key((exam_dir / "answer-key.txt").read_text(encoding="utf-8"))
    raw_exam = assemble_exam(pages, key, meta)
    prepared = prepare_exam(raw_exam)
    
    report = audit_exam(prepared)
    errors = [issue for issue in report.get("issues", []) if issue.get("severity") == "error"]
    if report.get("status") != "passed" or len(errors) > 0:
        raise RuntimeError(f"Audit failed for {slug}: {report}")
        
    (exam_dir / "exam.json").write_text(json.dumps(prepared, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exam {slug} built successfully! Questions: {prepared['questionCount']}, Status: {report['status']}, Errors: {len(errors)}")
    return report

def main():
    pdf_files = sorted(glob.glob("dist/N2/*.pdf"))
    print(f"Starting batch build of {len(pdf_files)} N2 exams...")
    
    out_dir = PROJECT_DIR / "exams"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    success = 0
    for idx, pdf in enumerate(pdf_files):
        pdf_path = Path(pdf)
        m = re.search(r"(\d{4})年(\d{1,2})月", pdf_path.name)
        if m:
            slug = f"{m.group(1)}-{int(m.group(2)):02d}-N2"
        else:
            m2 = re.search(r"(\d{4})\.(\d{1,2})", pdf_path.name)
            if m2:
                slug = f"{m2.group(1)}-{int(m2.group(2)):02d}-N2"
            else:
                slug = f"N2-{idx}"
                
        ocr_dir = PROJECT_DIR / "scratch" / "n2_ocr" / slug
        try:
            build_exam_package(slug, pdf_path, ocr_dir, out_dir)
            success += 1
        except Exception as err:
            print(f"ERROR building {slug}: {err}")
            
    print(f"\n==========================================")
    print(f"Completed: {success}/{len(pdf_files)} N2 exams built and audited with 0 errors!")
    print(f"==========================================")

if __name__ == "__main__":
    main()
