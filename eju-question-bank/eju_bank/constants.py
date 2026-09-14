"""EJU domain constants; deliberately independent from JLPT levels and parts."""

from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = 2
PAGE_CONTRACT_VERSION = 2

# 机器证明的署名。它与人的签名是两件事：人的签名说"我对照原页看过了"，
# 机器证明只说"流水线核对了它能核对的那几项"。用一个保留身份把两者在数据里分开，
# 任何人都不能把它当成人工复核，界面也据此向学习者说明这份卷的把关程度。
MACHINE_REVIEWER = "machine:eju-ocr-pipeline"
REVIEW_GRADES = ("HUMAN_SIGNED", "MACHINE_ATTESTED", "MIXED")
SOURCE_MANIFEST_VERSION = 1
DATABASE_SCHEMA_VERSION = 10

RIGHTS_STATUSES = frozenset(
    {
        "PRIVATE_STUDY",
        "INTERNAL_REVIEW",
        "PUBLIC_LICENSED",
        "COMMERCIAL_LICENSED",
        "SUSPENDED",
        "UNKNOWN",
        "REVIEW_REQUIRED",
    }
)

FILE_ROLES = frozenset(
    {
        "QUESTION_BOOKLET",
        "ANSWER_KEY",
        "AUDIO",
        "TRANSCRIPT",
        "OTHER",
    }
)

ANSWER_TYPES = frozenset({"SINGLE_CHOICE", "DIGIT_GRID", "ESSAY"})

BLOCK_KINDS = frozenset(
    {
        "form-start",
        "group-start",
        "material",
        "question",
        "writing-prompt",
        "answer-entry",
        "instruction",
        "ignored",
    }
)

AST_NODE_TYPES = frozenset(
    {
        "text",
        "paragraph",
        "inlineMath",
        "displayMath",
        "table",
        "figure",
        "callout",
        "underline",
        "ruby",
        "answerSlot",
        "lineBreak",
    }
)

COMPLETENESS_LEVELS = frozenset({"COMPLETE", "PARTIAL", "SAMPLE"})
AVAILABLE_MODES = frozenset({"PRACTICE", "SECTION", "MOCK"})

WRONG_QUESTION_STATES = frozenset(
    {
        "NEW_WRONG",
        "REVIEWING",
        "RETRY_DUE",
        "MASTERED",
    }
)

SESSION_EVENT_TYPES = frozenset(
    {
        "CREATE",
        "ANSWER",
        "BATCH_ANSWER",
        "PAUSE",
        "RESUME",
        "SUBMIT",
        "ABANDON",
    }
)

PIPELINE_STATUSES = frozenset(
    {
        "DISCOVERED",
        "RIGHTS_CHECKED",
        "RECEIVED",
        "PROBED",
        "RENDERED",
        "EXTRACTED",
        "REVIEWING",
        "REVIEWED",
        "ASSEMBLED",
        "AUDITED",
        "PUBLISHED",
        "BLOCKED_RIGHTS",
        "MISSING_SOURCE",
        "MISSING_ANSWER",
        "MISSING_AUDIO",
        "REVIEW_FAILED",
    }
)


@dataclass(frozen=True)
class FormSpec:
    code: str
    subject: str
    language: str
    course: str | None
    duration_sec: int
    score_max: int
    shared_timing_group: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _form(
    code: str,
    subject: str,
    language: str,
    duration_sec: int,
    score_max: int,
    *,
    course: str | None = None,
    shared_timing_group: str | None = None,
) -> FormSpec:
    return FormSpec(
        code=code,
        subject=subject,
        language=language,
        course=course,
        duration_sec=duration_sec,
        score_max=score_max,
        shared_timing_group=shared_timing_group,
    )


FORM_SPECS: dict[str, FormSpec] = {
    "JAPANESE_JA": _form("JAPANESE_JA", "JAPANESE", "ja", 7_500, 450),
    "PHYSICS_JA": _form("PHYSICS_JA", "PHYSICS", "ja", 4_800, 100, shared_timing_group="SCIENCE"),
    "PHYSICS_EN": _form("PHYSICS_EN", "PHYSICS", "en", 4_800, 100, shared_timing_group="SCIENCE"),
    "CHEMISTRY_JA": _form("CHEMISTRY_JA", "CHEMISTRY", "ja", 4_800, 100, shared_timing_group="SCIENCE"),
    "CHEMISTRY_EN": _form("CHEMISTRY_EN", "CHEMISTRY", "en", 4_800, 100, shared_timing_group="SCIENCE"),
    "BIOLOGY_JA": _form("BIOLOGY_JA", "BIOLOGY", "ja", 4_800, 100, shared_timing_group="SCIENCE"),
    "BIOLOGY_EN": _form("BIOLOGY_EN", "BIOLOGY", "en", 4_800, 100, shared_timing_group="SCIENCE"),
    "JAPAN_AND_WORLD_JA": _form("JAPAN_AND_WORLD_JA", "JAPAN_AND_WORLD", "ja", 4_800, 200),
    "JAPAN_AND_WORLD_EN": _form("JAPAN_AND_WORLD_EN", "JAPAN_AND_WORLD", "en", 4_800, 200),
    "MATHEMATICS_COURSE_1_JA": _form(
        "MATHEMATICS_COURSE_1_JA", "MATHEMATICS", "ja", 4_800, 200, course="COURSE_1"
    ),
    "MATHEMATICS_COURSE_1_EN": _form(
        "MATHEMATICS_COURSE_1_EN", "MATHEMATICS", "en", 4_800, 200, course="COURSE_1"
    ),
    "MATHEMATICS_COURSE_2_JA": _form(
        "MATHEMATICS_COURSE_2_JA", "MATHEMATICS", "ja", 4_800, 200, course="COURSE_2"
    ),
    "MATHEMATICS_COURSE_2_EN": _form(
        "MATHEMATICS_COURSE_2_EN", "MATHEMATICS", "en", 4_800, 200, course="COURSE_2"
    ),
}

SCIENCE_SUBJECTS = frozenset({"PHYSICS", "CHEMISTRY", "BIOLOGY"})
BASIC_SUBJECTS = SCIENCE_SUBJECTS | frozenset({"JAPAN_AND_WORLD", "MATHEMATICS"})
SOURCE_SUBJECTS = frozenset({"JAPANESE", "SCIENCE", "JAPAN_AND_WORLD", "MATHEMATICS"})

JAPANESE_SECTION_DURATIONS = {
    "WRITING": 1_800,
    "READING": 2_400,
    "LISTENING_READING_AND_LISTENING": 3_300,
}

ALLOWED_DIGIT_TOKENS = tuple(["-"] + [str(number) for number in range(10)])
