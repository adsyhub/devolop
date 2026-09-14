"""JLPT N1/N2 Official Domain Models, Classification Matrices, and Constraints.

Based on:
- 《JLPT N1/N2 真题题库系统——最终可执行规格》（docs/题库）
- 《JLPT 题库差距分析与执行计划》（docs/JLPT_题库差距分析与执行计划.md）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Level(str, Enum):
    N1 = "N1"
    N2 = "N2"


VALID_LEVELS = frozenset({Level.N1.value, Level.N2.value})


class TestSection(str, Enum):
    """Real exam timed test sections (限时科目)."""
    LANGUAGE_READING = "LANGUAGE_READING"  # 语言知识（文字・词汇・语法）・阅读
    LISTENING = "LISTENING"                # 听力


class ScoreSection(str, Enum):
    """Score report score categories (得分类别: 0~60分)."""
    LANGUAGE_KNOWLEDGE = "LANGUAGE_KNOWLEDGE"  # 言語知識 (0~60)
    READING = "READING"                        # 読解 (0~60)
    LISTENING = "LISTENING"                    # 聴解 (0~60)


class LearningSubject(str, Enum):
    """Study navigation subject classifications (学习分类)."""
    VOCABULARY = "VOCABULARY"  # 文字・词汇
    GRAMMAR = "GRAMMAR"        # 语法
    READING = "READING"        # 阅读
    LISTENING = "LISTENING"    # 听力


class AuthenticityStatus(str, Enum):
    OFFICIAL_ORIGINAL = "OFFICIAL_ORIGINAL"            # 官方实际考卷
    OFFICIAL_SAMPLE = "OFFICIAL_SAMPLE"                # 官方试题例
    OFFICIAL_PRACTICE_BOOK = "OFFICIAL_PRACTICE_BOOK"  # 官方公式问题集
    UNOFFICIAL = "UNOFFICIAL"                          # 非官方素材


class Completeness(str, Enum):
    FULL_SESSION = "FULL_SESSION"            # 单场完整原卷
    PARTIAL_SELECTION = "PARTIAL_SELECTION"  # 官方选编/部分题目


class PracticeMode(str, Enum):
    STRICT_EXAM = "STRICT_EXAM"                  # 严格限时模考
    PAPER_PRACTICE = "PAPER_PRACTICE"            # 整套真题练习
    SECTION_PRACTICE = "SECTION_PRACTICE"        # 按科目练习
    ITEM_TYPE_PRACTICE = "ITEM_TYPE_PRACTICE"    # 按官方题型练习
    TOPIC_PRACTICE = "TOPIC_PRACTICE"            # 按内部专题练习
    WRONG_REDO = "WRONG_REDO"                    # 错题重做
    BOOKMARK_PRACTICE = "BOOKMARK_PRACTICE"      # 收藏练习
    DUE_REVIEW = "DUE_REVIEW"                    # 到期复习
    REVIEW = "REVIEW"                            # 学习回顾


class FeedbackPolicy(str, Enum):
    IMMEDIATE = "IMMEDIATE"            # 选完立刻看
    GROUP_SUBMIT = "GROUP_SUBMIT"      # 题组提交后看
    SESSION_SUBMIT = "SESSION_SUBMIT"  # 整卷/整场提交后看


class MasteryStatus(str, Enum):
    NEW_WRONG = "NEW_WRONG"
    WRONG_AGAIN = "WRONG_AGAIN"
    CORRECT_ON_REDO = "CORRECT_ON_REDO"
    STABILIZING = "STABILIZING"
    MASTERED = "MASTERED"


@dataclass(frozen=True)
class ItemTypeSpec:
    code: str
    name_ja: str
    name_zh: str
    test_section: TestSection
    score_section: ScoreSection
    learning_subject: LearningSubject
    n1_allowed: bool
    n2_allowed: bool


# Official item type matrix per section 3.4
ITEM_TYPE_MATRIX: dict[str, ItemTypeSpec] = {
    # 文字词汇
    "VOCAB_KANJI_READING": ItemTypeSpec(
        code="VOCAB_KANJI_READING",
        name_ja="漢字読み",
        name_zh="汉字读音",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "VOCAB_ORTHOGRAPHY": ItemTypeSpec(
        code="VOCAB_ORTHOGRAPHY",
        name_ja="表記",
        name_zh="表记",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=False,  # K03: N1 不出现表记
        n2_allowed=True,
    ),
    "VOCAB_WORD_FORMATION": ItemTypeSpec(
        code="VOCAB_WORD_FORMATION",
        name_ja="語形成",
        name_zh="构词",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=False,  # K04: N1 不出现构词
        n2_allowed=True,
    ),
    "VOCAB_CONTEXT": ItemTypeSpec(
        code="VOCAB_CONTEXT",
        name_ja="文脈規定",
        name_zh="语境词汇",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "VOCAB_PARAPHRASE": ItemTypeSpec(
        code="VOCAB_PARAPHRASE",
        name_ja="言い換え類義",
        name_zh="近义替换",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "VOCAB_USAGE": ItemTypeSpec(
        code="VOCAB_USAGE",
        name_ja="用法",
        name_zh="词语用法",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.VOCABULARY,
        n1_allowed=True,
        n2_allowed=True,
    ),

    # 语法
    "GRAMMAR_FORM": ItemTypeSpec(
        code="GRAMMAR_FORM",
        name_ja="文法形式の判断",
        name_zh="语法形式判断",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.GRAMMAR,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "GRAMMAR_SENTENCE_COMPOSITION": ItemTypeSpec(
        code="GRAMMAR_SENTENCE_COMPOSITION",
        name_ja="文の組み立て",
        name_zh="句子组成",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.GRAMMAR,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "GRAMMAR_TEXT": ItemTypeSpec(
        code="GRAMMAR_TEXT",
        name_ja="文章の文法",
        name_zh="文章语法",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.LANGUAGE_KNOWLEDGE,
        learning_subject=LearningSubject.GRAMMAR,
        n1_allowed=True,
        n2_allowed=True,
    ),

    # 阅读
    "READING_SHORT": ItemTypeSpec(
        code="READING_SHORT",
        name_ja="内容理解（短文）",
        name_zh="短篇阅读",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "READING_MID": ItemTypeSpec(
        code="READING_MID",
        name_ja="内容理解（中文）",
        name_zh="中篇阅读",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "READING_LONG": ItemTypeSpec(
        code="READING_LONG",
        name_ja="内容理解（長文）",
        name_zh="长篇阅读",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=False,  # K05: N2 不出现独立长篇阅读
    ),
    "READING_INTEGRATED": ItemTypeSpec(
        code="READING_INTEGRATED",
        name_ja="統合理解",
        name_zh="综合理解",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "READING_THEMATIC_LONG": ItemTypeSpec(
        code="READING_THEMATIC_LONG",
        name_ja="主張理解（長文）",
        name_zh="主题理解",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "READING_INFORMATION_RETRIEVAL": ItemTypeSpec(
        code="READING_INFORMATION_RETRIEVAL",
        name_ja="情報検索",
        name_zh="信息检索",
        test_section=TestSection.LANGUAGE_READING,
        score_section=ScoreSection.READING,
        learning_subject=LearningSubject.READING,
        n1_allowed=True,
        n2_allowed=True,
    ),

    # 听力
    "LISTENING_TASK_BASED": ItemTypeSpec(
        code="LISTENING_TASK_BASED",
        name_ja="課題理解",
        name_zh="课题理解",
        test_section=TestSection.LISTENING,
        score_section=ScoreSection.LISTENING,
        learning_subject=LearningSubject.LISTENING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "LISTENING_KEY_POINTS": ItemTypeSpec(
        code="LISTENING_KEY_POINTS",
        name_ja="ポイント理解",
        name_zh="要点理解",
        test_section=TestSection.LISTENING,
        score_section=ScoreSection.LISTENING,
        learning_subject=LearningSubject.LISTENING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "LISTENING_GENERAL_OUTLINE": ItemTypeSpec(
        code="LISTENING_GENERAL_OUTLINE",
        name_ja="概要理解",
        name_zh="概要理解",
        test_section=TestSection.LISTENING,
        score_section=ScoreSection.LISTENING,
        learning_subject=LearningSubject.LISTENING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "LISTENING_QUICK_RESPONSE": ItemTypeSpec(
        code="LISTENING_QUICK_RESPONSE",
        name_ja="即時応答",
        name_zh="即时应答",
        test_section=TestSection.LISTENING,
        score_section=ScoreSection.LISTENING,
        learning_subject=LearningSubject.LISTENING,
        n1_allowed=True,
        n2_allowed=True,
    ),
    "LISTENING_INTEGRATED": ItemTypeSpec(
        code="LISTENING_INTEGRATED",
        name_ja="統合理解",
        name_zh="综合理解",
        test_section=TestSection.LISTENING,
        score_section=ScoreSection.LISTENING,
        learning_subject=LearningSubject.LISTENING,
        n1_allowed=True,
        n2_allowed=True,
    ),
}

# Forbidden item types that must never be accepted for N1 or N2
FORBIDDEN_ITEM_TYPES = frozenset({
    "LISTENING_VERBAL_EXPRESSIONS",
    "LISTENING_QUICK_RESPONSE_PICTURE",
})


def validate_level(level: str) -> str:
    """K01/K02: Validate that level is strictly N1 or N2."""
    lvl = str(level or "").strip().upper()
    if lvl not in VALID_LEVELS:
        raise ValueError(f"Level must be one of {sorted(VALID_LEVELS)}, got {level!r}.")
    return lvl


def validate_item_type(level: str, item_type_code: str) -> ItemTypeSpec:
    """K01~K08: Validate level and item type combinations."""
    lvl = validate_level(level)
    code = str(item_type_code or "").strip()

    if code in FORBIDDEN_ITEM_TYPES:
        raise ValueError(f"Item type {code!r} is forbidden for JLPT {lvl}.")

    spec = ITEM_TYPE_MATRIX.get(code)
    if spec is None:
        raise ValueError(f"Unknown item type: {item_type_code!r}.")

    if lvl == Level.N1.value and not spec.n1_allowed:
        raise ValueError(f"Item type {code} ({spec.name_zh}) is not allowed in N1.")
    if lvl == Level.N2.value and not spec.n2_allowed:
        raise ValueError(f"Item type {code} ({spec.name_zh}) is not allowed in N2.")

    return spec


@dataclass(frozen=True)
class BlueprintSection:
    section_code: TestSection
    display_order: int
    time_limit_sec: int
    allow_seek: bool = False
    allow_rate_change: bool = False
    allow_pause: bool = False
    allow_replay: bool = False


@dataclass(frozen=True)
class ExamBlueprint:
    level: str
    name: str
    version: int
    sections: list[BlueprintSection]


# Section 3.1 official timed blueprints (E01~E04)
OFFICIAL_BLUEPRINTS: dict[str, ExamBlueprint] = {
    "N1": ExamBlueprint(
        level="N1",
        name="JLPT N1 Official Standard Blueprint",
        version=1,
        sections=[
            BlueprintSection(
                section_code=TestSection.LANGUAGE_READING,
                display_order=1,
                time_limit_sec=110 * 60,  # 6600 seconds = 110 minutes
            ),
            BlueprintSection(
                section_code=TestSection.LISTENING,
                display_order=2,
                time_limit_sec=55 * 60,   # 3300 seconds = 55 minutes
                allow_seek=False,
                allow_rate_change=False,
                allow_pause=False,
                allow_replay=False,
            ),
        ],
    ),
    "N2": ExamBlueprint(
        level="N2",
        name="JLPT N2 Official Standard Blueprint",
        version=1,
        sections=[
            BlueprintSection(
                section_code=TestSection.LANGUAGE_READING,
                display_order=1,
                time_limit_sec=105 * 60,  # 6300 seconds = 105 minutes
            ),
            BlueprintSection(
                section_code=TestSection.LISTENING,
                display_order=2,
                time_limit_sec=50 * 60,   # 3000 seconds = 50 minutes
                allow_seek=False,
                allow_rate_change=False,
                allow_pause=False,
                allow_replay=False,
            ),
        ],
    ),
}


def get_blueprint(level: str) -> ExamBlueprint:
    lvl = validate_level(level)
    return OFFICIAL_BLUEPRINTS[lvl]

