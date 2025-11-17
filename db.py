import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("QUEST_DB_PATH", Path(__file__).parent / "quest.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn, table: str, column: str, definition: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cur.fetchall()}
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_date TEXT,
            commission_name TEXT,
            webcast_id TEXT,
            source_questions_json TEXT,
            transcript_text TEXT,
            agenda_file_path TEXT,
            transcript_file_path TEXT,
            processing_state TEXT DEFAULT 'pending',
            processing_started_at TEXT,
            processing_completed_at TEXT,
            processing_error TEXT,
            total_questions INTEGER DEFAULT 0,
            processed_questions INTEGER DEFAULT 0
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER,

            dossier_id TEXT,
            dossier_year_nr TEXT,
            sequence_nr TEXT,

            title TEXT,
            subject TEXT,
            roi_type TEXT,

            submitter_given_name TEXT,
            submitter_family_name TEXT,
            submitter_faction TEXT,

            assignee_label TEXT,
            assignee_given_name TEXT,
            assignee_family_name TEXT,

            question_start_time TEXT,
            question_end_time TEXT,
            answer_start_time TEXT,
            answer_end_time TEXT,
            reply_start_time TEXT,
            reply_end_time TEXT,

            question_text_raw TEXT,
            answer_text_verbatim TEXT,
            answer_text_raw TEXT,
            question_text_xml TEXT,

            summary TEXT,
            actions_json TEXT,
            topics_json TEXT,
            note TEXT,
            answer_status TEXT DEFAULT 'draft',
            processing_state TEXT DEFAULT 'pending',
            processing_started_at TEXT,
            processing_completed_at TEXT,
            processing_error TEXT,
            processing_attempts INTEGER DEFAULT 0,
            source_question_idx INTEGER,
            group_root_question_id INTEGER,
            group_label TEXT,

            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )"""
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS councillors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            given_name TEXT,
            family_name TEXT,
            name_with_title TEXT,
            wrong_spellings TEXT,
            UNIQUE(given_name, family_name)
        )"""
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_councillors_given_family ON councillors(given_name, family_name)"
    )

    cur.execute(
        """CREATE TABLE IF NOT EXISTS question_followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            speaker_given_name TEXT,
            speaker_family_name TEXT,
            speaker_faction TEXT,
            type TEXT,
            note TEXT,
            text TEXT,
            start_time TEXT,
            end_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )"""
    )

    _ensure_column(conn, "questions", "question_text_xml", "TEXT")
    _ensure_column(conn, "questions", "answer_text_verbatim", "TEXT")
    _ensure_column(conn, "questions", "answer_status", "TEXT DEFAULT 'draft'")
    _ensure_column(conn, "meetings", "source_questions_json", "TEXT")
    _ensure_column(conn, "meetings", "transcript_text", "TEXT")
    _ensure_column(conn, "meetings", "agenda_file_path", "TEXT")
    _ensure_column(conn, "meetings", "transcript_file_path", "TEXT")
    _ensure_column(conn, "meetings", "processing_state", "TEXT DEFAULT 'pending'")
    _ensure_column(conn, "meetings", "processing_started_at", "TEXT")
    _ensure_column(conn, "meetings", "processing_completed_at", "TEXT")
    _ensure_column(conn, "meetings", "processing_error", "TEXT")
    _ensure_column(conn, "meetings", "total_questions", "INTEGER DEFAULT 0")
    _ensure_column(conn, "meetings", "processed_questions", "INTEGER DEFAULT 0")

    _ensure_column(conn, "questions", "processing_state", "TEXT DEFAULT 'pending'")
    _ensure_column(conn, "questions", "processing_started_at", "TEXT")
    _ensure_column(conn, "questions", "processing_completed_at", "TEXT")
    _ensure_column(conn, "questions", "processing_error", "TEXT")
    _ensure_column(conn, "questions", "processing_attempts", "INTEGER DEFAULT 0")
    _ensure_column(conn, "questions", "source_question_idx", "INTEGER")
    _ensure_column(conn, "questions", "group_root_question_id", "INTEGER")
    _ensure_column(conn, "questions", "group_label", "TEXT")

    conn.commit()
    conn.close()


def upsert_councillor(conn, given_name: str, family_name: str, name_with_title: str, wrong_spellings: str = ""):
    given = (given_name or "").strip()
    family = (family_name or "").strip()
    titled = (name_with_title or "").strip()
    wrongs = (wrong_spellings or "").strip()

    if not (given or family or titled):
        return

    conn.execute(
        """INSERT INTO councillors (given_name, family_name, name_with_title, wrong_spellings)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(given_name, family_name)
           DO UPDATE SET
             name_with_title = CASE
               WHEN LENGTH(TRIM(excluded.name_with_title)) > 0 THEN excluded.name_with_title
               ELSE councillors.name_with_title
             END,
             wrong_spellings = CASE
               WHEN LENGTH(TRIM(excluded.wrong_spellings)) > 0 THEN excluded.wrong_spellings
               ELSE councillors.wrong_spellings
             END
        """,
        (given, family, titled, wrongs),
    )


def list_councillors(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT id, given_name, family_name, name_with_title, wrong_spellings
           FROM councillors
           ORDER BY family_name, given_name"""
    )
    return [dict(row) for row in cur.fetchall()]


if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
