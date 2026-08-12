import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "lessons.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lesson_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        topic TEXT,
        level TEXT,
        lesson_json TEXT,
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def ensure_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO sessions (session_id, created_at) VALUES (?, ?)",
            (session_id, now_iso())
        )
        conn.commit()
    conn.close()


def save_message(session_id, role, content):
    ensure_session(session_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now_iso())
    )
    conn.commit()
    conn.close()


def get_history(session_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    history = [{"role": row["role"], "content": row["content"]} for row in rows]
    return history[-limit:]


def save_lesson_version(session_id, topic, level, lesson_json):
    ensure_session(session_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lesson_versions (session_id, topic, level, lesson_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, topic, level, json.dumps(lesson_json), now_iso())
    )
    conn.commit()
    version_id = cursor.lastrowid
    conn.close()
    return version_id


def load_lesson_version(version_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lesson_versions WHERE id = ?", (version_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    result["lesson_json"] = json.loads(result["lesson_json"])
    return result


def list_lesson_versions(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, topic, level, created_at FROM lesson_versions WHERE session_id = ? ORDER BY id DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()

    save_message("test-session", "user", "Generate the lesson")
    save_message("test-session", "assistant", "Here is your lesson pack")
    print("History:", get_history("test-session"))

    version_id = save_lesson_version("test-session", "Python Loops", "beginner", {"title": "Test Lesson"})
    print("Saved version ID:", version_id)
    print("Loaded back:", load_lesson_version(version_id))
    print("All versions:", list_lesson_versions("test-session"))