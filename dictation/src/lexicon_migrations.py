"""Ordered, individually recorded lexicon migrations; never replace the learner's database.

Each version is a separate step with its own row in ``lex_schema``. A step that fails
rolls back and leaves no "migration complete" marker, so the run can simply be repeated
after the cause is fixed (§5.4). Every step must be safe to re-run on a copy.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS lex_schema(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lex_card_overrides(
 vocab_id TEXT NOT NULL REFERENCES vocab(id) ON DELETE CASCADE,
 field TEXT NOT NULL, PRIMARY KEY(vocab_id, field));
CREATE TABLE IF NOT EXISTS lex_daily_batch_runs(
 deck_id TEXT NOT NULL REFERENCES lex_decks(id) ON DELETE CASCADE,
 local_day TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(deck_id,local_day));
CREATE TABLE IF NOT EXISTS lex_deck_settings(
 deck_id TEXT PRIMARY KEY REFERENCES lex_decks(id) ON DELETE CASCADE,
 settings_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS lex_user_entries(
 source_ref TEXT PRIMARY KEY, data_json TEXT NOT NULL DEFAULT '{}',
 version INTEGER NOT NULL DEFAULT 1, deleted INTEGER NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lex_entry_sources(
 source_ref TEXT NOT NULL, context_key TEXT NOT NULL, data_json TEXT NOT NULL,
 PRIMARY KEY(source_ref,context_key));
CREATE TABLE IF NOT EXISTS lex_sessions(
 id TEXT PRIMARY KEY, mode TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
 config_json TEXT NOT NULL, items_json TEXT NOT NULL,
 state_json TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 creation_key TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS lex_attempts(
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES lex_sessions(id),
 item_id TEXT NOT NULL, round INTEGER NOT NULL DEFAULT 0,
 source_ref TEXT NOT NULL, kind TEXT NOT NULL, exercise_type TEXT NOT NULL,
 answer_json TEXT NOT NULL, result_json TEXT NOT NULL,
 operation_id TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
 UNIQUE(session_id,item_id,round));
CREATE INDEX IF NOT EXISTS lex_attempt_source ON lex_attempts(source_ref,created_at);
CREATE INDEX IF NOT EXISTS lex_attempt_session ON lex_attempts(session_id);
CREATE TABLE IF NOT EXISTS lex_review_events(
 operation_id TEXT PRIMARY KEY, vocab_id TEXT NOT NULL,
 before_json TEXT NOT NULL, after_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lex_mistakes(
 source_ref TEXT NOT NULL, exercise_type TEXT NOT NULL,
 kind TEXT NOT NULL, wrong_count INTEGER NOT NULL DEFAULT 0,
 clean_streak INTEGER NOT NULL DEFAULT 0, resolved INTEGER NOT NULL DEFAULT 0,
 last_attempt_id TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(source_ref,exercise_type));
CREATE TABLE IF NOT EXISTS lex_question_feedback(
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL, item_id TEXT NOT NULL,
 message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL);
"""

# LEX-02 / LEX-03: a deletion is an intent that has to outlive the row, and an
# operation receipt only counts as a duplicate when it names the same target and
# the same request body.
IDENTITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS lex_card_tombstones(
 vocab_id TEXT PRIMARY KEY, source_ref TEXT NOT NULL DEFAULT '',
 prompt_type TEXT NOT NULL DEFAULT '', variant_key TEXT NOT NULL DEFAULT '',
 deleted_at TEXT NOT NULL, operation_id TEXT NOT NULL UNIQUE,
 version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS lex_identity_aliases(
 old_vocab_id TEXT PRIMARY KEY, canonical_vocab_id TEXT NOT NULL,
 reason TEXT NOT NULL, migration_version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS lex_migration_reports(
 id INTEGER PRIMARY KEY AUTOINCREMENT, migration_version INTEGER NOT NULL,
 kind TEXT NOT NULL, detail_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lex_reveals(
 operation_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, item_id TEXT NOT NULL,
 round INTEGER NOT NULL DEFAULT 0, sequence INTEGER NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(session_id,item_id,round));
"""

# Tables the learner's own work lives in; any of them being non-empty is reason to back up.
LEARNER_TABLES = ('vocab', 'notes', 'progress', 'study_logs', 'punch_records',
                  'lex_decks', 'lex_sessions', 'lex_user_entries', 'lex_attempts')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def report(conn: sqlite3.Connection, version: int, kind: str, detail: dict) -> None:
    """Record something a migration could not decide on its own, instead of guessing."""
    conn.execute(
        "INSERT INTO lex_migration_reports(migration_version,kind,detail_json,created_at) VALUES (?,?,?,?)",
        (version, kind, json.dumps(detail, ensure_ascii=False), _now()),
    )


def _v1_workspace_tables(conn: sqlite3.Connection, _db_path: Path) -> None:
    conn.executescript(SCHEMA)
    # Preserve legacy editable fields rather than guessing which were authored.
    conn.execute("INSERT OR IGNORE INTO lex_card_overrides SELECT id, 'note' FROM vocab WHERE source_ref<>''")
    conn.execute("INSERT OR IGNORE INTO lex_card_overrides SELECT id, 'tags' FROM vocab WHERE source_ref<>''")
    # Name the columns: a later migration adds more, and an implicit list breaks on re-run.
    conn.execute("INSERT OR IGNORE INTO lex_daily_batch_runs(deck_id,local_day,created_at)"
                 " SELECT deck_id,local_day,MIN(served_at) FROM lex_daily_batches GROUP BY deck_id,local_day")


def _v2_deletion_and_versions(conn: sqlite3.Connection, _db_path: Path) -> None:
    conn.executescript(IDENTITY_SCHEMA)
    _add_column(conn, 'vocab', 'review_version', 'INTEGER NOT NULL DEFAULT 0')
    _add_column(conn, 'vocab_review_receipts', 'request_digest', "TEXT NOT NULL DEFAULT ''")
    _add_column(conn, 'vocab_review_receipts', 'redirected_from', "TEXT NOT NULL DEFAULT ''")
    _add_column(conn, 'lex_attempts', 'request_digest', "TEXT NOT NULL DEFAULT ''")
    _add_column(conn, 'lex_attempts', 'sequence', 'INTEGER NOT NULL DEFAULT 0')
    _add_column(conn, 'lex_review_events', 'request_digest', "TEXT NOT NULL DEFAULT ''")
    # Existing attempts predate sequencing; order them by the order they were written.
    for session_id, in conn.execute("SELECT DISTINCT session_id FROM lex_attempts WHERE sequence=0").fetchall():
        for position, (attempt_id,) in enumerate(
            conn.execute("SELECT id FROM lex_attempts WHERE session_id=? ORDER BY rowid", (session_id,)).fetchall(), 1
        ):
            conn.execute("UPDATE lex_attempts SET sequence=? WHERE id=?", (position, attempt_id))
    # A card that already carries review history starts at a version its client cannot guess.
    conn.execute("UPDATE vocab SET review_version=1 WHERE review_version=0 AND last_reviewed_at<>''")


def _v4_batch_configuration(conn: sqlite3.Connection, _db_path: Path) -> None:
    """Record what a day's batch was generated under, so later edits cannot rewrite it."""
    for column, definition in (
        ("study_timezone", "TEXT NOT NULL DEFAULT ''"),
        ("quota_unit", "TEXT NOT NULL DEFAULT 'card'"),
        ("daily_new", "INTEGER NOT NULL DEFAULT 0"),
        ("settings_version", "TEXT NOT NULL DEFAULT ''"),
    ):
        _add_column(conn, 'lex_daily_batch_runs', column, definition)
    conn.execute(
        "UPDATE lex_daily_batch_runs SET study_timezone = COALESCE("
        "(SELECT study_timezone FROM lex_decks d WHERE d.id = lex_daily_batch_runs.deck_id), '')"
        " WHERE study_timezone = ''"
    )


def _v5_feedback_triage(conn: sqlite3.Connection, _db_path: Path) -> None:
    """Make a reported problem traceable and its resolution recorded (LEX-15, §10.3)."""
    for column, definition in (
        ('source_ref', "TEXT NOT NULL DEFAULT ''"),
        ('question_id', "TEXT NOT NULL DEFAULT ''"),
        ('answer_version', "TEXT NOT NULL DEFAULT ''"),
        ('exercise_type', "TEXT NOT NULL DEFAULT ''"),
        ('variant_key', "TEXT NOT NULL DEFAULT ''"),
        ('resolution', "TEXT NOT NULL DEFAULT ''"),
        ('resolved_by', "TEXT NOT NULL DEFAULT ''"),
        ('resolved_at', "TEXT NOT NULL DEFAULT ''"),
        ('revision_ref', "TEXT NOT NULL DEFAULT ''"),
        ('note', "TEXT NOT NULL DEFAULT ''"),
    ):
        _add_column(conn, 'lex_question_feedback', column, definition)
    # An attempt against an answer later found wrong is history, not evidence. It keeps
    # its row and stops counting, rather than being deleted or replayed over (§10.3).
    _add_column(conn, 'lex_attempts', 'validity', "TEXT NOT NULL DEFAULT 'valid'")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS lex_withdrawn_questions(
     source_ref TEXT NOT NULL, question_id TEXT NOT NULL DEFAULT '',
     exercise_type TEXT NOT NULL DEFAULT '', answer_version TEXT NOT NULL DEFAULT '',
     reason TEXT NOT NULL, feedback_id TEXT NOT NULL DEFAULT '',
     withdrawn_by TEXT NOT NULL DEFAULT '', withdrawn_at TEXT NOT NULL,
     PRIMARY KEY(source_ref, question_id, answer_version));
    CREATE TABLE IF NOT EXISTS lex_srs_corrections(
     id INTEGER PRIMARY KEY AUTOINCREMENT, vocab_id TEXT NOT NULL,
     source_ref TEXT NOT NULL, reason TEXT NOT NULL, proposal_json TEXT NOT NULL,
     status TEXT NOT NULL DEFAULT 'proposed', created_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS lex_attempt_validity ON lex_attempts(validity);
    """)


def _review_rank(row: sqlite3.Row) -> tuple:
    return (1 if row['last_reviewed_at'] else 0, str(row['last_reviewed_at'] or ''),
            int(row['srs_repetitions'] or 0))


def _retarget(conn: sqlite3.Connection, old_id: str, canonical: str) -> None:
    """Point every relation, batch, event and receipt at the canonical card."""
    conn.execute("INSERT OR IGNORE INTO lex_card_overrides SELECT ?, field FROM lex_card_overrides WHERE vocab_id=?",
                 (canonical, old_id))
    conn.execute("DELETE FROM lex_card_overrides WHERE vocab_id=?", (old_id,))
    conn.execute("UPDATE OR IGNORE lex_deck_cards SET vocab_id=? WHERE vocab_id=?", (canonical, old_id))
    # Only rows a unique constraint refused are left; they have no valid target.
    conn.execute("UPDATE lex_deck_cards SET vocab_id=NULL WHERE vocab_id=?", (old_id,))
    conn.execute("UPDATE OR IGNORE lex_daily_batches SET vocab_id=? WHERE vocab_id=?", (canonical, old_id))
    conn.execute("DELETE FROM lex_daily_batches WHERE vocab_id=?", (old_id,))
    conn.execute("UPDATE lex_review_events SET vocab_id=? WHERE vocab_id=?", (canonical, old_id))
    # The original response body stays untouched; the redirect is recorded beside it.
    conn.execute("UPDATE vocab_review_receipts SET vocab_id=?, redirected_from=? WHERE vocab_id=?",
                 (canonical, old_id, old_id))


def _v3_merge_duplicate_cards(conn: sqlite3.Connection, _db_path: Path) -> None:
    """Fold the `<promptType>-default` cards practice used to mint onto the plan card.

    Both halves are the same ability, so they become one card, but the merge never
    invents a combined history: it keeps every event and adopts the state of whichever
    side was reviewed last (§4.4).
    """
    from local_backend import source_card_id

    timestamp = _now()
    legacy = [row for row in conn.execute("SELECT * FROM vocab WHERE source_ref<>''").fetchall()
              if str(row['variant_key'] or '') == f"{row['prompt_type'] or 'recall'}-default"]
    for row in legacy:
        prompt = str(row['prompt_type'] or 'recall')
        canonical = source_card_id(str(row['source_ref']), prompt, 'default')
        if canonical == row['id']:
            continue
        target = conn.execute("SELECT * FROM vocab WHERE id=?", (canonical,)).fetchone()
        if target is None:
            # The id is a parent key: copy the row under the new id, move the children
            # onto it, then drop the old one. Updating it in place would trip the
            # foreign key and silently detach the plan's relations.
            columns = [info[1] for info in conn.execute("PRAGMA table_info(vocab)")]
            projected = ", ".join(
                "?" if column in {'id', 'variant_key', 'updated_at'} else column for column in columns
            )
            values = []
            for column in columns:
                if column == 'id':
                    values.append(canonical)
                elif column == 'variant_key':
                    values.append('default')
                elif column == 'updated_at':
                    values.append(timestamp)
            conn.execute(
                f"INSERT OR IGNORE INTO vocab({', '.join(columns)}) SELECT {projected} FROM vocab WHERE id=?",
                (*values, row['id']),
            )
            _retarget(conn, row['id'], canonical)
            conn.execute("DELETE FROM vocab WHERE id=?", (row['id'],))
            reason = 'auto-variant-renamed'
        else:
            keep = row if _review_rank(row) > _review_rank(target) else target
            conflicts = {field: [row[field], target[field]] for field in
                         ('term', 'reading', 'meaning', 'note', 'tags', 'level')
                         if str(row[field] or '') != str(target[field] or '')}
            conn.execute(
                """UPDATE vocab SET srs_repetitions=?, srs_interval=?, srs_ease=?, srs_stage=?,
                   srs_lapses=?, next_review_at=?, last_reviewed_at=?, mastered=?,
                   review_suspended=?, review_version=review_version+1, updated_at=? WHERE id=?""",
                (keep['srs_repetitions'], keep['srs_interval'], keep['srs_ease'], keep['srs_stage'],
                 max(int(row['srs_lapses'] or 0), int(target['srs_lapses'] or 0)),
                 keep['next_review_at'], keep['last_reviewed_at'], keep['mastered'],
                 # A pause on either half is kept; resuming has to be a deliberate act.
                 1 if (row['review_suspended'] or target['review_suspended']) else 0,
                 timestamp, canonical),
            )
            _retarget(conn, row['id'], canonical)
            conn.execute("DELETE FROM vocab WHERE id=?", (row['id'],))
            reason = 'auto-variant-merged'
            if conflicts:
                # Both original values are kept verbatim so the learner can restore either.
                report(conn, 3, 'card-merge-field-conflict',
                       {'canonicalVocabId': canonical, 'oldVocabId': row['id'],
                        'sourceRef': row['source_ref'], 'promptType': prompt, 'fields': conflicts})
        conn.execute("INSERT OR REPLACE INTO lex_identity_aliases VALUES (?,?,?,?)",
                     (row['id'], canonical, reason, 3))


MIGRATIONS: tuple[tuple[int, object], ...] = (
    (1, _v1_workspace_tables),
    (2, _v2_deletion_and_versions),
    (3, _v3_merge_duplicate_cards),
    (4, _v4_batch_configuration),
    (5, _v5_feedback_triage),
)
VERSION = MIGRATIONS[-1][0]


def _backup(conn: sqlite3.Connection, db_path: Path, version: int) -> None:
    for table in LEARNER_TABLES:
        try:
            populated = bool(conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone())
        except sqlite3.OperationalError:
            continue
        if not populated:
            continue
        backup_path = Path(str(db_path) + f".before-lexicon-v{version}.bak")
        if not backup_path.exists():
            # sqlite backup includes a consistent snapshot even if the source uses WAL.
            with sqlite3.connect(str(backup_path)) as target:
                conn.backup(target)
        return


def migrate(conn: sqlite3.Connection, db_path: Path) -> list[int]:
    """Apply every migration this build knows and the database has not recorded."""
    conn.execute("CREATE TABLE IF NOT EXISTS lex_schema(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
    conn.commit()
    applied = {row[0] for row in conn.execute("SELECT version FROM lex_schema")}
    pending = [(version, run) for version, run in MIGRATIONS if version not in applied]
    if not pending:
        return []
    _backup(conn, db_path, pending[0][0])
    done = []
    for version, run in pending:
        try:
            run(conn, db_path)
            conn.execute("INSERT OR IGNORE INTO lex_schema VALUES (?,?)", (version, _now()))
            conn.commit()
        except Exception:
            # Leaving no marker is what makes the failed step repeatable.
            conn.rollback()
            raise
        done.append(version)
    return done
