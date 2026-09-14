"""从原卷文件名读出它是哪一套卷。

制课台上传一个 PDF 之后要知道：哪一年、第几回、什么科目、是题册还是答案册。
文件名里通常写着（``2023平成35年第2回数学2.pdf``），但**不总是**：理综和日语的
答案册叫 ``2002平成14年第1回答案.pdf``，里面没有科目。所以这里只做推断，
把拿不准的项留空，由页面上的人确认 —— 猜一个科目比留空危险得多。

``scripts/batch_process.py`` 早就有一套按目录分科的推断。那套靠的是 PAPER/ 的
目录结构，上传路径没有目录可依。两边的产物必须一致，所以 inventoryId、
expectedForms、syllabusVersion 的拼法在这里统一定义，批处理脚本里的同名规则
与此对齐。
"""

from __future__ import annotations

import re
from typing import Any

SUBJECTS = ("SCIENCE", "MATHEMATICS", "JAPAN_AND_WORLD", "JAPANESE")
COURSES = ("COURSE_1", "COURSE_2")
ROLES = ("QUESTION_BOOKLET", "ANSWER_KEY")

SHORT_NAME = {
    ("MATHEMATICS", "COURSE_1"): "math-c1",
    ("MATHEMATICS", "COURSE_2"): "math-c2",
    ("SCIENCE", None): "science",
    ("JAPAN_AND_WORLD", None): "japan-world",
    ("JAPANESE", None): "japanese",
}

# 文件名里的科目说法。顺序有讲究：「数学2」要在「数学」之前判掉。
_SUBJECT_HINTS: tuple[tuple[str, str, str | None], ...] = (
    ("数学1", "MATHEMATICS", "COURSE_1"),
    ("数学１", "MATHEMATICS", "COURSE_1"),
    ("文科数学", "MATHEMATICS", "COURSE_1"),
    ("数学2", "MATHEMATICS", "COURSE_2"),
    ("数学２", "MATHEMATICS", "COURSE_2"),
    ("理科数学", "MATHEMATICS", "COURSE_2"),
    ("理综", "SCIENCE", None),
    ("理科", "SCIENCE", None),
    ("综合科目", "JAPAN_AND_WORLD", None),
    ("総合科目", "JAPAN_AND_WORLD", None),
    ("文综", "JAPAN_AND_WORLD", None),
    ("日语", "JAPANESE", None),
    ("日本語", "JAPANESE", None),
)


def parse_session(name: str) -> tuple[int | None, int | None]:
    """读出西历年份与第几回。读不出就是 None，不拿今年顶上。"""
    year_match = re.search(r"(19|20)\d{2}", name)
    year = int(year_match.group(0)) if year_match else None
    session_match = re.search(r"第\s*([12一二])\s*回", name)
    if session_match:
        session = 1 if session_match.group(1) in ("1", "一") else 2
    else:
        # 有些年份只考一回，文件名里就不写回次了。
        session = 1 if year else None
    return year, session


def parse_subject(name: str) -> tuple[str | None, str | None]:
    for hint, subject, course in _SUBJECT_HINTS:
        if hint in name:
            return subject, course
    return None, None


def parse_role(name: str) -> str:
    return "ANSWER_KEY" if ("答案" in name or "正解" in name) else "QUESTION_BOOKLET"


def syllabus_version(subject: str | None, year: int | None) -> str | None:
    if not subject or not year:
        return None
    if subject == "JAPANESE":
        return "japanese-2015" if year >= 2015 else "japanese-2002"
    return "basic-2015" if year >= 2015 else "basic-2002"


def expected_forms(subject: str | None, course: str | None, language: str = "ja") -> list[str]:
    lang = language.upper()
    if subject == "SCIENCE":
        return [f"PHYSICS_{lang}", f"CHEMISTRY_{lang}", f"BIOLOGY_{lang}"]
    if subject == "MATHEMATICS" and course:
        return [f"MATHEMATICS_{course}_{lang}"]
    if subject == "JAPAN_AND_WORLD":
        return [f"JAPAN_AND_WORLD_{lang}"]
    if subject == "JAPANESE":
        return ["JAPANESE_JA"]
    return []


def short_name(subject: str, course: str | None) -> str:
    return SHORT_NAME.get((subject, course if subject == "MATHEMATICS" else None),
                          subject.lower())


def work_dir_name(session: str, subject: str, course: str | None) -> str:
    return f"{session}-{short_name(subject, course)}"


def inventory_id(session: str, subject: str, course: str | None, language: str) -> str:
    return f"eju-{session}-{short_name(subject, course)}-{language}"


def describe(filename: str) -> dict[str, Any]:
    """一个上传文件的推断结果。拿不准的项是 None，页面据此提示要人来填。"""
    stem = filename.rsplit("/", 1)[-1]
    year, ordinal = parse_session(stem)
    subject, course = parse_subject(stem)
    role = parse_role(stem)
    session = f"{year}-{ordinal}" if year and ordinal else None
    language = "ja"
    missing = [key for key, value in
               (("year", year), ("session", ordinal), ("subject", subject)) if not value]
    if subject == "MATHEMATICS" and not course:
        missing.append("course")
    return {
        "fileName": stem,
        "year": year,
        "ordinal": ordinal,
        "session": session,
        "subject": subject,
        "course": course,
        "language": language,
        "role": role,
        "syllabusVersion": syllabus_version(subject, year),
        "expectedForms": expected_forms(subject, course, language),
        "inventoryId": inventory_id(session, subject, course, language)
                       if session and subject else None,
        "workDir": work_dir_name(session, subject, course) if session and subject else None,
        "needsConfirmation": missing,
    }
