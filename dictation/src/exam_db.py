"""JLPT Question Bank Database Engine and Versioned Tables.

Implements Section 16 database schemas, immutable version policies (V06),
database constraints for level and item types (K08), and SQLite/PostgreSQL compatibility.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exam_models import (
    ITEM_TYPE_MATRIX,
    VALID_LEVELS,
    AuthenticityStatus,
    Completeness,
    Level,
    PracticeMode,
    TestSection,
)

V2_SCHEMA_SQL = """
-- 1. Users and Roles
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('LEARNER', 'CONTENT_EDITOR', 'ANSWER_REVIEWER', 'RIGHTS_REVIEWER', 'PUBLISHER', 'ADMIN')),
    status        TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- 2. Sources and Licenses
CREATE TABLE IF NOT EXISTS content_sources (
    id                  TEXT PRIMARY KEY,
    code                TEXT UNIQUE NOT NULL,
    name                TEXT NOT NULL,
    source_type         TEXT NOT NULL,
    authenticity_status TEXT NOT NULL CHECK(authenticity_status IN ('OFFICIAL_ORIGINAL', 'OFFICIAL_SAMPLE', 'OFFICIAL_PRACTICE_BOOK', 'UNOFFICIAL')),
    completeness        TEXT NOT NULL CHECK(completeness IN ('FULL_SESSION', 'PARTIAL_SELECTION')),
    exam_year           INTEGER,
    exam_month          INTEGER,
    notes               TEXT NOT NULL DEFAULT '',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS licenses (
    id                      TEXT PRIMARY KEY,
    content_source_id       TEXT NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    rights_status           TEXT NOT NULL CHECK(rights_status IN ('UNAPPROVED', 'APPROVED', 'SUSPENDED', 'EXPIRED', 'REVOKED')),
    copyright_owner         TEXT NOT NULL DEFAULT '',
    license_holder          TEXT NOT NULL DEFAULT '',
    commercial_use_allowed  INTEGER NOT NULL DEFAULT 0,
    translation_allowed     INTEGER NOT NULL DEFAULT 0,
    audio_streaming_allowed INTEGER NOT NULL DEFAULT 0,
    valid_from              TEXT NOT NULL,
    valid_until             TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

-- 3. Materials
CREATE TABLE IF NOT EXISTS materials (
    id                TEXT PRIMARY KEY,
    stable_code       TEXT UNIQUE NOT NULL,
    material_type     TEXT NOT NULL CHECK(material_type IN ('TEXT', 'AUDIO', 'IMAGE', 'TABLE', 'MIXED')),
    content_source_id TEXT NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS material_versions (
    id               TEXT PRIMARY KEY,
    material_id      TEXT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    version_number   INTEGER NOT NULL,
    plain_text       TEXT NOT NULL DEFAULT '',
    content_ast_json TEXT NOT NULL DEFAULT '{}',
    content_hash     TEXT NOT NULL,
    status           TEXT NOT NULL CHECK(status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')),
    created_at       TEXT NOT NULL,
    published_at     TEXT,
    UNIQUE(material_id, version_number)
);

-- 4. Question Groups (K08: DB-level checks on level and item_type)
CREATE TABLE IF NOT EXISTS question_groups (
    id                TEXT PRIMARY KEY,
    stable_code       TEXT UNIQUE NOT NULL,
    level             TEXT NOT NULL CHECK(level IN ('N1', 'N2')),
    learning_subject  TEXT NOT NULL CHECK(learning_subject IN ('VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING')),
    item_type_code    TEXT NOT NULL,
    content_source_id TEXT NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    created_at        TEXT NOT NULL,
    -- Hard DB constraint K08
    CHECK(
        (level = 'N1' AND item_type_code NOT IN ('VOCAB_ORTHOGRAPHY', 'VOCAB_WORD_FORMATION', 'LISTENING_VERBAL_EXPRESSIONS')) OR
        (level = 'N2' AND item_type_code NOT IN ('READING_LONG', 'LISTENING_VERBAL_EXPRESSIONS'))
    )
);

CREATE TABLE IF NOT EXISTS question_group_versions (
    id                 TEXT PRIMARY KEY,
    question_group_id  TEXT NOT NULL REFERENCES question_groups(id) ON DELETE CASCADE,
    version_number     INTEGER NOT NULL,
    instruction_text   TEXT NOT NULL DEFAULT '',
    status             TEXT NOT NULL CHECK(status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED')),
    content_hash       TEXT NOT NULL,
    created_at         TEXT NOT NULL,
    published_at       TEXT,
    UNIQUE(question_group_id, version_number)
);

CREATE TABLE IF NOT EXISTS question_group_materials (
    question_group_version_id TEXT NOT NULL REFERENCES question_group_versions(id) ON DELETE CASCADE,
    material_version_id       TEXT NOT NULL REFERENCES material_versions(id) ON DELETE CASCADE,
    display_order             INTEGER NOT NULL,
    usage_type                TEXT NOT NULL CHECK(usage_type IN ('PRIMARY', 'SUPPLEMENT', 'IMAGE', 'AUDIO', 'TRANSCRIPT')),
    PRIMARY KEY (question_group_version_id, material_version_id)
);

CREATE TABLE IF NOT EXISTS questions (
    id                TEXT PRIMARY KEY,
    question_group_id TEXT NOT NULL REFERENCES question_groups(id) ON DELETE CASCADE,
    stable_key        TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_versions (
    id                        TEXT PRIMARY KEY,
    question_id               TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    version_number            INTEGER NOT NULL,
    question_group_version_id TEXT NOT NULL REFERENCES question_group_versions(id) ON DELETE CASCADE,
    display_order             INTEGER NOT NULL,
    stem_text                 TEXT NOT NULL,
    stem_ast_json             TEXT NOT NULL DEFAULT '{}',
    answer_type               TEXT NOT NULL DEFAULT 'SINGLE_CHOICE',
    correct_answer_json       TEXT NOT NULL,
    explanation_zh            TEXT NOT NULL DEFAULT '',
    explanation_ja            TEXT NOT NULL DEFAULT '',
    status                    TEXT NOT NULL CHECK(status IN ('DRAFT', 'APPROVED', 'PUBLISHED', 'ARCHIVED')),
    content_hash              TEXT NOT NULL,
    created_at                TEXT NOT NULL,
    published_at              TEXT,
    UNIQUE(question_id, version_number)
);

CREATE TABLE IF NOT EXISTS option_versions (
    id                   TEXT PRIMARY KEY,
    question_version_id  TEXT NOT NULL REFERENCES question_versions(id) ON DELETE CASCADE,
    option_key           INTEGER NOT NULL,
    display_order        INTEGER NOT NULL,
    content_text         TEXT NOT NULL,
    is_correct           INTEGER NOT NULL DEFAULT 0,
    UNIQUE(question_version_id, option_key),
    UNIQUE(question_version_id, display_order)
);

-- 5. Papers and Paper Versions
CREATE TABLE IF NOT EXISTS papers (
    id                TEXT PRIMARY KEY,
    stable_code       TEXT UNIQUE NOT NULL,
    title             TEXT NOT NULL,
    level             TEXT NOT NULL CHECK(level IN ('N1', 'N2')),
    content_source_id TEXT NOT NULL REFERENCES content_sources(id) ON DELETE CASCADE,
    completeness      TEXT NOT NULL CHECK(completeness IN ('FULL_SESSION', 'PARTIAL_SELECTION')),
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_versions (
    id             TEXT PRIMARY KEY,
    paper_id       TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title          TEXT NOT NULL,
    status         TEXT NOT NULL CHECK(status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED', 'SUSPENDED')),
    content_hash   TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    published_at   TEXT,
    UNIQUE(paper_id, version_number)
);

CREATE TABLE IF NOT EXISTS paper_sections (
    id               TEXT PRIMARY KEY,
    paper_version_id TEXT NOT NULL REFERENCES paper_versions(id) ON DELETE CASCADE,
    section_code     TEXT NOT NULL CHECK(section_code IN ('LANGUAGE_READING', 'LISTENING')),
    display_order    INTEGER NOT NULL,
    time_limit_sec   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_parts (
    id               TEXT PRIMARY KEY,
    paper_section_id TEXT NOT NULL REFERENCES paper_sections(id) ON DELETE CASCADE,
    part_code        TEXT NOT NULL,
    title            TEXT NOT NULL,
    item_type_code   TEXT NOT NULL,
    display_order    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_blocks (
    id                        TEXT PRIMARY KEY,
    paper_part_id             TEXT NOT NULL REFERENCES paper_parts(id) ON DELETE CASCADE,
    question_group_version_id TEXT NOT NULL REFERENCES question_group_versions(id) ON DELETE RESTRICT,
    display_order             INTEGER NOT NULL
);

-- 6. Practice Sessions & Server-side Authoritative State
CREATE TABLE IF NOT EXISTS practice_sessions (
    id                          TEXT PRIMARY KEY,
    user_id                     TEXT NOT NULL,
    level                       TEXT NOT NULL CHECK(level IN ('N1', 'N2')),
    mode                        TEXT NOT NULL,
    paper_version_id            TEXT REFERENCES paper_versions(id),
    status                      TEXT NOT NULL CHECK(status IN ('INITIALIZED', 'IN_PROGRESS', 'SECTION_LOCKED', 'SUBMITTED', 'EXPIRED')),
    active_lease_token          TEXT NOT NULL DEFAULT '',
    random_seed                 INTEGER NOT NULL DEFAULT 0,
    selection_algorithm_version TEXT NOT NULL DEFAULT 'v1',
    started_at                  TEXT,
    submitted_at                TEXT,
    expires_at                  TEXT,
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_sections (
    id                  TEXT PRIMARY KEY,
    practice_session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    section_code        TEXT NOT NULL,
    display_order       INTEGER NOT NULL,
    status              TEXT NOT NULL CHECK(status IN ('PENDING', 'IN_PROGRESS', 'SUBMITTED', 'EXPIRED')),
    started_at          TEXT,
    deadline_at         TEXT,
    submitted_at        TEXT
);

CREATE TABLE IF NOT EXISTS session_group_snapshots (
    id                        TEXT PRIMARY KEY,
    practice_session_id       TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    session_section_id        TEXT NOT NULL REFERENCES session_sections(id) ON DELETE CASCADE,
    question_group_version_id TEXT NOT NULL REFERENCES question_group_versions(id),
    display_order             INTEGER NOT NULL,
    required_question_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at                TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_records (
    id                  TEXT PRIMARY KEY,
    practice_session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_version_id TEXT NOT NULL REFERENCES question_versions(id),
    chosen_option_key   INTEGER,
    is_uncertain        INTEGER NOT NULL DEFAULT 0,
    confidence          TEXT NOT NULL DEFAULT '',
    version             INTEGER NOT NULL DEFAULT 1,
    first_answered_at   TEXT NOT NULL,
    last_answered_at    TEXT NOT NULL,
    server_received_at  TEXT NOT NULL,
    UNIQUE(practice_session_id, question_version_id)
);

CREATE TABLE IF NOT EXISTS answer_events (
    id                  TEXT PRIMARY KEY,
    practice_session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_version_id TEXT NOT NULL REFERENCES question_versions(id),
    event_type          TEXT NOT NULL,
    payload_hash        TEXT NOT NULL,
    idempotency_key     TEXT NOT NULL,
    client_time         TEXT NOT NULL,
    server_time         TEXT NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS result_snapshots (
    id                     TEXT PRIMARY KEY,
    practice_session_id    TEXT UNIQUE NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    calculation_version    TEXT NOT NULL DEFAULT 'v1',
    raw_correct_count      INTEGER NOT NULL,
    raw_total_count        INTEGER NOT NULL,
    raw_accuracy           REAL NOT NULL,
    score_sections_json    TEXT NOT NULL,
    item_type_stats_json   TEXT NOT NULL,
    time_stats_json        TEXT NOT NULL,
    estimate_model_version TEXT,
    created_at             TEXT NOT NULL
);

-- 7. User SRS States
CREATE TABLE IF NOT EXISTS user_question_states (
    user_id          TEXT NOT NULL,
    question_id      TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    first_attempt_at TEXT NOT NULL,
    last_attempt_at  TEXT NOT NULL,
    attempt_count    INTEGER NOT NULL DEFAULT 0,
    correct_count    INTEGER NOT NULL DEFAULT 0,
    wrong_count      INTEGER NOT NULL DEFAULT 0,
    last_result      TEXT NOT NULL DEFAULT '',
    mastery_status   TEXT NOT NULL DEFAULT 'NEW_WRONG',
    streak           INTEGER NOT NULL DEFAULT 0,
    next_review_at   TEXT NOT NULL DEFAULT '',
    updated_at       TEXT NOT NULL,
    PRIMARY KEY(user_id, question_id)
);

-- 8. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id           TEXT PRIMARY KEY,
    actor_id     TEXT NOT NULL,
    action       TEXT NOT NULL,
    target_type  TEXT NOT NULL,
    target_id    TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL
);

-- 9. V06: Database Triggers Enforcing Immutability on Published Versions
CREATE TRIGGER IF NOT EXISTS trg_paper_versions_immutable
BEFORE UPDATE ON paper_versions
FOR EACH ROW
WHEN OLD.status = 'PUBLISHED'
BEGIN
    SELECT RAISE(FAIL, 'Cannot update a published paper version (V06 immutable version policy).');
END;

CREATE TRIGGER IF NOT EXISTS trg_question_group_versions_immutable
BEFORE UPDATE ON question_group_versions
FOR EACH ROW
WHEN OLD.status = 'PUBLISHED'
BEGIN
    SELECT RAISE(FAIL, 'Cannot update a published question group version (V06 immutable version policy).');
END;

CREATE TRIGGER IF NOT EXISTS trg_question_versions_immutable
BEFORE UPDATE ON question_versions
FOR EACH ROW
WHEN OLD.status = 'PUBLISHED'
BEGIN
    SELECT RAISE(FAIL, 'Cannot update a published question version (V06 immutable version policy).');
END;
"""


class ExamDatabase:
    """Manages the versioned database schema and connection."""

    def __init__(self, connection: sqlite3.Connection, lock: threading.RLock | None = None) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.lock = lock if lock is not None else threading.RLock()
        with self.lock:
            self.connection.executescript(V2_SCHEMA_SQL)
            self.connection.commit()

    @classmethod
    def in_memory(cls) -> "ExamDatabase":
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        return cls(conn)

    @classmethod
    def from_path(cls, db_path: Path) -> "ExamDatabase":
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        return cls(conn)

