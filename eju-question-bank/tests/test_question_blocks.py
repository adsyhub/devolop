"""The page parser must read the two real option layouts and refuse to guess."""
from eju_bank.ocr.question_blocks import parse_questions

# Trimmed from work/2002-1-japan-world/ocr_cache/p0007.json — circled numbers
# arrive from OCR as LaTeX \textcircled{n}.
LATEX_PAGE = r"""総合科目一5

問5 円高の影響についての説明として最も適切なものを，次の$\textcircled{1}$～$\textcircled{4}$の中から1つ選びなさい。

$\textcircled{1}$ 円高によって，輸入品の円表示価格が低下する。
$\textcircled{2}$ 円高によって，貿易収支の黒字幅は縮小する。
$\textcircled{3}$ 円高は，国内不況をもたらす。
$\textcircled{4}$ 円高によって，輸出品の外貨表示価格が上昇する。

- 101 -
"""

# Trimmed from work/2009-1-japanese/ocr_cache — plain numbered options.
PLAIN_PAGE = """問1

次の文章は，ある研究者が若者に向けて書いたものです。筆者は何が一番大切だと言っていますか。

21世紀は君たちの時代。自分で価値観をつくり，責任を持って生きていってほしい。

1. 優れた個人が「私」のためだけに働くこと
2. 優れた個人が先生から多くのことを学ぶこと
3. 優れた個人が社会に貢献すること
4. 優れた個人が諸悪の根源を見きわめること

- 15 -
"""

# Trimmed from work/2002-1-japan-world/ocr_cache/p0008.json.
SHARED_PASSAGE_PAGE = r"""問7 次の文章を読み，下の問い(1), (2)に答えなさい。

企業や消費者が，市場の外で社会に不利益をもたらすことを「外部不経済」という。

(1) 外部不経済の事例として不適切なものを，次の$\textcircled{1}$～$\textcircled{4}$の中から1つ選びなさい。14

$\textcircled{1}$ 工場で自動車を生産したが，売れ残ってしまった。
$\textcircled{2}$ 産業廃棄物から有害物質が発生した。
$\textcircled{3}$ 夜間の騒音がはげしくなった。
$\textcircled{4}$ ホームでの喫煙で空気が汚れた。

(2) 公共財の事例として正しいものを，次の$\textcircled{1}$～$\textcircled{4}$の中から1つ選びなさい。15

$\textcircled{1}$ リソート・ホテル
$\textcircled{2}$ 水資源
$\textcircled{3}$ 労働力
$\textcircled{4}$ 河川の堤防
"""

# The exam front matter uses a numbered list that must not read as options.
FRONT_MATTER = """試験全体に関する注意

1. 解答は，解答用紙に鉛筆（HB）で記入してください。
2. 記述の解答は，記述用の解答用紙に日本語で書いてください。
3. 解答用紙に書いてある注意事項も必ず読んでください。
4. 各領域の解答は，係員の指示にしたがって始めてください。
"""


def test_reads_latex_circled_options():
    questions = parse_questions(LATEX_PAGE)
    assert len(questions) == 1
    q = questions[0]
    assert q["label"] == "問5"
    assert q["stem"].startswith("円高の影響についての説明")
    # The internal marker must not leak into displayed text.
    assert "textcircled" not in q["stem"] and "⟦" not in q["stem"]
    assert "①" in q["stem"]
    assert list(q["options"]) == ["1", "2", "3", "4"]
    assert q["options"]["1"] == "円高によって，輸入品の円表示価格が低下する。"


def test_reads_plain_numbered_options():
    questions = parse_questions(PLAIN_PAGE)
    assert len(questions) == 1
    assert questions[0]["label"] == "問1"
    assert questions[0]["options"]["3"] == "優れた個人が社会に貢献すること"


def test_sub_questions_keep_their_own_stem_and_share_the_passage():
    questions = parse_questions(SHARED_PASSAGE_PAGE)
    assert [q["label"] for q in questions] == ["問7(1)", "問7(2)"]
    # The printed answer-sheet number is the join key against the 正解表.
    assert [q["slot"] for q in questions] == ["14", "15"]
    assert questions[0]["stem"].startswith("外部不経済の事例として")
    assert "外部不経済" in questions[0]["context"]
    # The shared passage belongs to both sub-questions, not to one stem.
    assert questions[0]["context"] == questions[1]["context"]
    assert questions[1]["options"]["4"] == "河川の堤防"


def test_front_matter_numbered_list_is_not_a_question():
    assert parse_questions(FRONT_MATTER) == []


def test_incomplete_options_are_dropped_not_padded():
    """Options continuing onto the next page must not become a 2-option question."""
    page = (
        r"問8 正しいものを，次の$\textcircled{1}$～$\textcircled{4}$の中から1つ選びなさい。16" "\n"
        r"$\textcircled{1}$ 甲" "\n"
        r"$\textcircled{3}$ 乙" "\n"
    )
    assert parse_questions(page) == []


def test_empty_page_yields_nothing():
    assert parse_questions("") == []
    assert parse_questions("- 42 -\n日本語-12\n") == []
