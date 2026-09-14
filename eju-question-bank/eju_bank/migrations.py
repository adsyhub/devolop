"""Database migration runner and schema definitions."""

from __future__ import annotations

import sqlite3
from .errors import MigrationError
from .constants import DATABASE_SCHEMA_VERSION
from .util import utc_now

MIGRATION_V1 = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    rights_status TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    stable_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_versions (
    id TEXT PRIMARY KEY,
    paper_id TEXT NOT NULL REFERENCES papers(id),
    version_number INTEGER NOT NULL,
    content_revision TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PUBLISHED','ARCHIVED','SUSPENDED')),
    channel TEXT NOT NULL CHECK(channel IN ('PRIVATE','PUBLIC','COMMERCIAL')),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT NOT NULL,
    UNIQUE(paper_id, version_number),
    UNIQUE(paper_id, content_revision)
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    stable_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_versions (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(id),
    paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),
    version_number INTEGER NOT NULL,
    form_code TEXT NOT NULL,
    answer_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    delivery_json TEXT NOT NULL,
    answer_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(question_id, paper_version_id)
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id TEXT PRIMARY KEY,
    paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),
    mode TEXT NOT NULL CHECK(mode IN ('MOCK','PRACTICE','SECTION')),
    selected_forms_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('IN_PROGRESS','PAUSED','SUBMITTED','ABANDONED')),
    created_at TEXT NOT NULL,
    submitted_at TEXT
);

CREATE TABLE IF NOT EXISTS responses (
    practice_session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(id),
    response_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(practice_session_id, question_id)
);

CREATE TABLE IF NOT EXISTS results (
    practice_session_id TEXT PRIMARY KEY REFERENCES practice_sessions(id) ON DELETE CASCADE,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS paper_versions_immutable
BEFORE UPDATE ON paper_versions
FOR EACH ROW WHEN OLD.status = 'PUBLISHED'
BEGIN
    SELECT RAISE(FAIL, 'Published paper versions are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS question_versions_immutable
BEFORE UPDATE ON question_versions
FOR EACH ROW
BEGIN
    SELECT RAISE(FAIL, 'Question versions are immutable.');
END;
"""

MIGRATION_V2_ADDITIONS = """
-- Media & assets
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    source_file_id TEXT,
    source_page INTEGER,
    source_bbox TEXT,
    derivative_type TEXT,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_assets (
    paper_version_id TEXT NOT NULL REFERENCES paper_versions(id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    usage_kind TEXT NOT NULL,
    PRIMARY KEY(paper_version_id, asset_id, usage_kind)
);

CREATE TABLE IF NOT EXISTS audio_cues (
    id TEXT PRIMARY KEY,
    track_asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    cue_id TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    lead_in_ms INTEGER DEFAULT 0,
    replay_policy TEXT DEFAULT 'ONCE',
    question_id TEXT REFERENCES questions(id),
    created_at TEXT NOT NULL
);

-- Source files and evidence
CREATE TABLE IF NOT EXISTS source_files (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_rights_evidence (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    note TEXT,
    basis TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL
);

-- Extraction and review
CREATE TABLE IF NOT EXISTS extraction_runs (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    revision TEXT,
    prompt_version TEXT,
    params_json TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS page_revisions (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES extraction_runs(id),
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    contract_json TEXT NOT NULL,
    signed_by TEXT,
    signed_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_decisions (
    id TEXT PRIMARY KEY,
    page_revision_id TEXT NOT NULL REFERENCES page_revisions(id) ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL,
    comments TEXT,
    diff_json TEXT,
    created_at TEXT NOT NULL
);

-- Session events stream
CREATE TABLE IF NOT EXISTS session_events (
    id TEXT PRIMARY KEY,
    practice_session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Learning enhancements: Bookmarks, Notes, Wrong questions, Explanations
CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    question_id TEXT UNIQUE NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS question_notes (
    id TEXT PRIMARY KEY,
    question_id TEXT UNIQUE NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wrong_question_state (
    question_id TEXT PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('NEW_WRONG','REVIEWING','RETRY_DUE','MASTERED')),
    wrong_count INTEGER DEFAULT 1,
    last_answered_at TEXT NOT NULL,
    next_review_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS explanations (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    language TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'REVIEWED', 'REJECTED')),
    author TEXT NOT NULL,
    content_ast_json TEXT NOT NULL,
    revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(question_id, language, revision)
);

CREATE TABLE IF NOT EXISTS backup_history (
    id TEXT PRIMARY KEY,
    backup_file TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None


def _has_column(conn: sqlite3.Connection, table_name: str, col_name: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    for row in cur.fetchall():
        if row[1] == col_name:
            return True
    return False


def _upgrade_practice_sessions_table(conn: sqlite3.Connection) -> None:
    # Check if practice_sessions has old CHECK constraint without PAUSED
    schema_sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='practice_sessions'").fetchone()
    if schema_sql and "PAUSED" not in schema_sql[0]:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("""
            CREATE TABLE practice_sessions_new (
                id TEXT PRIMARY KEY,
                paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),
                mode TEXT NOT NULL CHECK(mode IN ('MOCK','PRACTICE','SECTION')),
                selected_forms_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('IN_PROGRESS','PAUSED','SUBMITTED','ABANDONED')),
                active_duration_sec INTEGER DEFAULT 0,
                deadline TEXT,
                paused_at TEXT,
                last_active_at TEXT,
                created_at TEXT NOT NULL,
                submitted_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO practice_sessions_new (id, paper_version_id, mode, selected_forms_json, status, created_at, submitted_at)
            SELECT id, paper_version_id, mode, selected_forms_json, status, created_at, submitted_at FROM practice_sessions
        """)
        conn.execute("DROP TABLE practice_sessions")
        conn.execute("ALTER TABLE practice_sessions_new RENAME TO practice_sessions")
        conn.execute("PRAGMA foreign_keys = ON")


def _execute_script(conn: sqlite3.Connection, script: str) -> None:
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            conn.execute(statement)
            statement = ""
    if statement.strip():
        conn.execute(statement)


def migrate_database(conn: sqlite3.Connection) -> int:
    """Apply every schema change atomically, preserving legacy foreign keys."""
    if conn.in_transaction:
        raise MigrationError("Finish the current transaction before migration")
    if get_schema_version(conn) > DATABASE_SCHEMA_VERSION:
        raise MigrationError("Database schema is newer than this application")
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = _migrate_steps(conn)
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise MigrationError("Migration would leave broken foreign key references")
        conn.commit()
        return version
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _migrate_steps(conn: sqlite3.Connection) -> int:
    """Migrates database to latest schema version. Returns current version."""
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. Initialize schema_migrations table if absent
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)

    # Check current migration version
    cur = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
    current_ver = cur.fetchone()[0]

    # Check if legacy v1 tables exist without migration record
    if current_ver == 0:
        if _has_table(conn, "papers") and _has_table(conn, "paper_versions"):
            conn.execute(
                "INSERT INTO schema_migrations VALUES (1, 'initial_v1_baseline', ?)",
                (utc_now(),)
            )
            current_ver = 1
        else:
            # Fresh database: apply V1 baseline
            _execute_script(conn, MIGRATION_V1)
            conn.execute(
                "INSERT INTO schema_migrations VALUES (1, 'initial_v1_baseline', ?)",
                (utc_now(),)
            )
            current_ver = 1

    if current_ver < 2:
        # Upgrade practice_sessions table check constraints
        _upgrade_practice_sessions_table(conn)

        # Apply V2 additions
        _execute_script(conn, MIGRATION_V2_ADDITIONS)

        # In practice_sessions, ensure active_duration_sec, deadline, paused_at, last_active_at exist
        if not _has_column(conn, "practice_sessions", "active_duration_sec"):
            conn.execute("ALTER TABLE practice_sessions ADD COLUMN active_duration_sec INTEGER DEFAULT 0")
        if not _has_column(conn, "practice_sessions", "deadline"):
            conn.execute("ALTER TABLE practice_sessions ADD COLUMN deadline TEXT")
        if not _has_column(conn, "practice_sessions", "paused_at"):
            conn.execute("ALTER TABLE practice_sessions ADD COLUMN paused_at TEXT")
        if not _has_column(conn, "practice_sessions", "last_active_at"):
            conn.execute("ALTER TABLE practice_sessions ADD COLUMN last_active_at TEXT")

        # In paper_versions, ensure completeness, available_modes, syllabus_id exist
        if not _has_column(conn, "paper_versions", "completeness"):
            conn.execute("ALTER TABLE paper_versions ADD COLUMN completeness TEXT DEFAULT 'SAMPLE'")
        if not _has_column(conn, "paper_versions", "available_modes"):
            conn.execute("ALTER TABLE paper_versions ADD COLUMN available_modes TEXT DEFAULT '[\"PRACTICE\"]'")
        if not _has_column(conn, "paper_versions", "syllabus_id"):
            conn.execute("ALTER TABLE paper_versions ADD COLUMN syllabus_id TEXT DEFAULT 'basic-2015'")

        # In question_versions, ensure explanation_json and scoring_policy exist
        if not _has_column(conn, "question_versions", "explanation_json"):
            conn.execute("ALTER TABLE question_versions ADD COLUMN explanation_json TEXT")
        if not _has_column(conn, "question_versions", "scoring_policy"):
            conn.execute("ALTER TABLE question_versions ADD COLUMN scoring_policy TEXT DEFAULT 'ALL_OR_NOTHING'")

        conn.execute(
            "INSERT INTO schema_migrations VALUES (2, 'v2_media_events_learning_tables', ?)",
            (utc_now(),)
        )
        current_ver = 2

    if current_ver > DATABASE_SCHEMA_VERSION:
        raise MigrationError(f"Database schema {current_ver} is newer than supported {DATABASE_SCHEMA_VERSION}")
    if current_ver < 3:
        _execute_script(conn, """
            CREATE TABLE session_state (
                session_id TEXT PRIMARY KEY REFERENCES practice_sessions(id),
                response_version INTEGER NOT NULL DEFAULT 0,
                progress_json TEXT NOT NULL DEFAULT '{}',
                config_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE save_receipts (
                session_id TEXT NOT NULL REFERENCES practice_sessions(id),
                request_id TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                PRIMARY KEY (session_id, request_id)
            );
            CREATE TABLE paper_delivery_state (
                paper_version_id TEXT PRIMARY KEY REFERENCES paper_versions(id),
                state TEXT NOT NULL,
                note TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_session_history ON practice_sessions(created_at);
            CREATE INDEX IF NOT EXISTS idx_question_versions_paper ON question_versions(paper_version_id);
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (3, 'session_state_and_delivery', ?)", (utc_now(),))
        current_ver = 3

    if current_ver < 4:
        _execute_script(conn, """
            CREATE TABLE paper_reviews (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(id),
                content_digest TEXT NOT NULL,
                decision TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                page_revision_ids_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE paper_review_revocations (
                review_id TEXT PRIMARY KEY REFERENCES paper_reviews(id),
                reviewer TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TRIGGER signed_pages_immutable BEFORE UPDATE ON page_revisions
            WHEN OLD.signed_by IS NOT NULL BEGIN SELECT RAISE(FAIL,'Signed page is immutable'); END;
            CREATE TRIGGER signed_pages_no_delete BEFORE DELETE ON page_revisions
            WHEN OLD.signed_by IS NOT NULL BEGIN SELECT RAISE(FAIL,'Signed page is immutable'); END;
            CREATE TRIGGER paper_reviews_immutable BEFORE UPDATE ON paper_reviews
            BEGIN SELECT RAISE(FAIL,'Paper review is immutable'); END;
            CREATE TRIGGER paper_reviews_no_delete BEFORE DELETE ON paper_reviews
            BEGIN SELECT RAISE(FAIL,'Paper review is immutable'); END;
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (4, 'content_review_certificates', ?)", (utc_now(),))
        current_ver = 4

    if current_ver < 5:
        _execute_script(conn, """
            CREATE TABLE IF NOT EXISTS source_structure_revisions (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                revision INTEGER NOT NULL,
                structure_json TEXT NOT NULL,
                signed_by TEXT NOT NULL,
                signed_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(source_id, revision)
            );
            CREATE TRIGGER IF NOT EXISTS source_structures_immutable BEFORE UPDATE ON source_structure_revisions
            BEGIN SELECT RAISE(FAIL, 'Signed source structure revision is immutable'); END;
            CREATE TRIGGER IF NOT EXISTS source_structures_no_delete BEFORE DELETE ON source_structure_revisions
            BEGIN SELECT RAISE(FAIL, 'Signed source structure revision is immutable'); END;
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (5, 'source_structure_baselines', ?)", (utc_now(),))
        current_ver = 5

    if current_ver < 6:
        _execute_script(conn, """
CREATE TABLE library_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE jobs (id TEXT PRIMARY KEY, job_type TEXT NOT NULL,target_id TEXT NOT NULL,status TEXT NOT NULL,params_json TEXT NOT NULL,progress_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,lease_owner TEXT,lease_until TEXT);
CREATE TABLE job_events (id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),event_type TEXT NOT NULL,details_json TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE extraction_page_attempts (id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES extraction_runs(id),role TEXT NOT NULL,page_number INTEGER NOT NULL,attempt_number INTEGER NOT NULL,input_cache_key TEXT,output_digest TEXT,duration_ms INTEGER NOT NULL,status TEXT NOT NULL,error_code TEXT,error_message TEXT,created_at TEXT NOT NULL,UNIQUE(run_id,role,page_number,attempt_number));
CREATE TABLE asset_origins (id TEXT PRIMARY KEY,asset_id TEXT NOT NULL,source_id TEXT REFERENCES sources(id),source_hash TEXT,role TEXT,page_number INTEGER,bbox_json TEXT,transform_json TEXT NOT NULL,review_state TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE content_issues (id TEXT PRIMARY KEY,issue_type TEXT NOT NULL,question_id TEXT NOT NULL REFERENCES questions(id),question_version_id TEXT NOT NULL REFERENCES question_versions(id),paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),session_id TEXT REFERENCES practice_sessions(id),description TEXT NOT NULL,status TEXT NOT NULL,status_reason TEXT,reported_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE content_issue_events(id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES content_issues(id),status TEXT NOT NULL,reason TEXT,created_at TEXT NOT NULL);
CREATE TABLE attempt_facts(session_id TEXT NOT NULL REFERENCES practice_sessions(id),question_version_id TEXT NOT NULL REFERENCES question_versions(id),question_id TEXT NOT NULL REFERENCES questions(id),paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),form_code TEXT NOT NULL,answer_type TEXT NOT NULL,answered INTEGER NOT NULL,correct INTEGER,revealed INTEGER NOT NULL DEFAULT 0,scoring_version TEXT NOT NULL,submitted_at TEXT NOT NULL,PRIMARY KEY(session_id,question_version_id));
CREATE INDEX idx_attempt_question ON attempt_facts(question_id,submitted_at,session_id);
CREATE TABLE review_events(id TEXT PRIMARY KEY,question_id TEXT NOT NULL REFERENCES questions(id),old_status TEXT,new_status TEXT,due_at TEXT,days INTEGER,reason TEXT,session_id TEXT,created_at TEXT NOT NULL);
CREATE TABLE learning_goals(id TEXT PRIMARY KEY,config_json TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE publication_outbox(id TEXT PRIMARY KEY,paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),inventory_id TEXT,payload_json TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE question_search(question_version_id TEXT PRIMARY KEY REFERENCES question_versions(id),question_id TEXT NOT NULL,paper_version_id TEXT NOT NULL REFERENCES paper_versions(id),form_code TEXT NOT NULL,language TEXT NOT NULL,answer_type TEXT NOT NULL,search_text TEXT NOT NULL,metadata_json TEXT NOT NULL,sort_key TEXT NOT NULL);
CREATE INDEX idx_search_form ON question_search(form_code,sort_key,question_id);
CREATE TABLE explanation_revisions(id TEXT PRIMARY KEY,question_version_id TEXT NOT NULL REFERENCES question_versions(id),revision INTEGER NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL,reviewer TEXT,created_at TEXT NOT NULL,UNIQUE(question_version_id,revision));
CREATE TABLE essay_reviews(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES practice_sessions(id),question_id TEXT NOT NULL REFERENCES questions(id),revision INTEGER NOT NULL,kind TEXT NOT NULL,rubric_version TEXT NOT NULL,payload_json TEXT NOT NULL,reviewer TEXT,created_at TEXT NOT NULL,UNIQUE(session_id,question_id,kind,revision));
CREATE TABLE note_revisions(question_id TEXT NOT NULL REFERENCES questions(id),revision INTEGER NOT NULL,note_text TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(question_id,revision));
CREATE TABLE audio_tracks(id TEXT PRIMARY KEY,paper_version_id TEXT REFERENCES paper_versions(id),source_id TEXT REFERENCES sources(id),asset_id TEXT NOT NULL,duration_ms INTEGER NOT NULL,status TEXT NOT NULL,cues_json TEXT NOT NULL,reviewer TEXT,created_at TEXT NOT NULL);
CREATE TABLE session_audio_events(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES practice_sessions(id),track_id TEXT NOT NULL,action TEXT NOT NULL,position_ms INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE practice_previews(id TEXT PRIMARY KEY,payload_json TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL);
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (6, 'production_and_learning_workflows', ?)", (utc_now(),))
        current_ver = 6

    if current_ver < 7:
        _execute_script(conn,"""
ALTER TABLE session_state ADD COLUMN progress_version INTEGER NOT NULL DEFAULT 0;
CREATE TABLE rubric_revisions(id TEXT PRIMARY KEY,payload_json TEXT NOT NULL,reviewer TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE session_review_content(session_id TEXT NOT NULL REFERENCES practice_sessions(id),question_version_id TEXT NOT NULL REFERENCES question_versions(id),revision_id TEXT REFERENCES explanation_revisions(id),PRIMARY KEY(session_id,question_version_id));
CREATE TABLE action_receipts(scope TEXT NOT NULL,request_id TEXT NOT NULL,payload_hash TEXT NOT NULL,result_json TEXT NOT NULL,PRIMARY KEY(scope,request_id));
CREATE TRIGGER attempt_facts_immutable BEFORE UPDATE ON attempt_facts BEGIN SELECT RAISE(FAIL,'Attempt facts are immutable'); END;
CREATE TRIGGER essay_reviews_immutable BEFORE UPDATE ON essay_reviews BEGIN SELECT RAISE(FAIL,'Essay reviews are immutable'); END;
CREATE TRIGGER rubric_revisions_immutable BEFORE UPDATE ON rubric_revisions BEGIN SELECT RAISE(FAIL,'Rubrics are immutable'); END;
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (7,'versioned_learning_annotations',?)",(utc_now(),))
        current_ver=7

    if current_ver < 8:
        _execute_script(conn,"""
CREATE TABLE session_review_annotations (
 session_id TEXT NOT NULL REFERENCES practice_sessions(id),
 question_version_id TEXT NOT NULL REFERENCES question_versions(id),
 kind TEXT NOT NULL,language TEXT NOT NULL,
 revision_id TEXT NOT NULL REFERENCES explanation_revisions(id),
 PRIMARY KEY(session_id,question_version_id,kind,language)
);
INSERT INTO session_review_annotations
 SELECT c.session_id,c.question_version_id,json_extract(e.payload_json,'$.kind'),json_extract(e.payload_json,'$.language'),e.id
 FROM session_review_content c JOIN explanation_revisions e ON e.id=c.revision_id;
CREATE TRIGGER explanations_immutable BEFORE UPDATE ON explanation_revisions BEGIN SELECT RAISE(FAIL,'Explanation revisions are immutable'); END;
CREATE TRIGGER explanations_no_delete BEFORE DELETE ON explanation_revisions BEGIN SELECT RAISE(FAIL,'Explanation revisions are immutable'); END;
        """)
        conn.execute("INSERT INTO schema_migrations VALUES (8,'parallel_review_annotations',?)",(utc_now(),))
        current_ver=8

    if current_ver < 9:
        # 谁写的这一版修订。原来只有 signed_by，于是"人保存了但还没签"的草稿在
        # 数据里和机器产物长得一模一样，自动重跑会把它当自己的东西覆盖掉。
        # 历史行无从追认作者，一律留空并当作未知来源：不回填，也不假设是人。
        if not _has_column(conn, "page_revisions", "actor_kind"):
            conn.execute("ALTER TABLE page_revisions ADD COLUMN actor_kind TEXT")
        if not _has_column(conn, "page_revisions", "authored_by"):
            conn.execute("ALTER TABLE page_revisions ADD COLUMN authored_by TEXT")
        # 不回填历史行。已签页本来就不可变（signed page is immutable 触发器），
        # 而且它们的作者读 signed_by 就知道 —— human_locked() 正是这样兜底的。
        # 未签的历史行没有任何作者线索，留空，按未知来源处理，不假设是人。
        conn.execute("INSERT INTO schema_migrations VALUES (9,'page_revision_authorship',?)",
                     (utc_now(),))
        current_ver = 9

    if current_ver < 10:
        # 中断过几次、下一次什么时候可以再试。没有这两列，"自动恢复"要么不做，
        # 要么就是无限重试——同样的输入、同样的策略失败之后再跑一遍还是失败，
        # 只是把故障变成了忙等。
        if not _has_column(conn, "jobs", "attempts"):
            conn.execute("ALTER TABLE jobs ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")
        if not _has_column(conn, "jobs", "next_attempt_at"):
            conn.execute("ALTER TABLE jobs ADD COLUMN next_attempt_at TEXT")
        conn.execute("INSERT INTO schema_migrations VALUES (10,'job_retry_budget',?)",
                     (utc_now(),))
        current_ver = 10

    # Always ensure practice_sessions table check constraint is up-to-date even if v2 already marked
    _upgrade_practice_sessions_table(conn)

    return current_ver


def get_schema_version(conn: sqlite3.Connection) -> int:
    if not _has_table(conn, "schema_migrations"):
        if _has_table(conn, "papers"):
            return 1
        return 0
    cur = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
    return int(cur.fetchone()[0])
