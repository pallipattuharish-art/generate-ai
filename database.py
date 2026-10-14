"""
SQLite database management for AI Study Assistant.
Handles saving, searching, retrieving, and deleting study materials and quiz results.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from config import Config


def get_db_path():
    """Return database file path and ensure directory exists."""
    db_path = Config.DATABASE_PATH
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_db_connection(custom_path=None):
    """Create and return a configured SQLite connection."""
    path = custom_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(custom_path=None):
    """Initialize database tables with appropriate indexes."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        material_type TEXT NOT NULL,
        content_json TEXT NOT NULL,
        source_snippet TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        percentage REAL NOT NULL,
        time_spent_seconds INTEGER DEFAULT 0,
        details_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_subject ON materials(subject);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(material_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_created ON materials(created_at);")

    conn.commit()
    conn.close()


def save_material(title, subject, material_type, content, source_snippet=None, custom_path=None):
    """
    Save a new study material to the database.
    content can be a dict/list (which will be JSON-serialized) or a string.
    """
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    content_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    title = (title or "Untitled Study Note").strip()
    subject = (subject or "General").strip()

    cursor.execute("""
        INSERT INTO materials (title, subject, material_type, content_json, source_snippet, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        subject,
        material_type,
        content_str,
        source_snippet,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    material_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return material_id


def get_all_materials(search_query=None, material_type=None, custom_path=None):
    """Retrieve saved materials with optional search query and type filter."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    query = "SELECT id, title, subject, material_type, source_snippet, created_at FROM materials WHERE 1=1"
    params = []

    if search_query:
        query += " AND (title LIKE ? OR subject LIKE ?)"
        like_arg = f"%{search_query.strip()}%"
        params.extend([like_arg, like_arg])

    if material_type and material_type != "all":
        query += " AND material_type = ?"
        params.append(material_type)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_material_by_id(material_id, custom_path=None):
    """Retrieve a single material with its full content by ID."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    try:
        data["content"] = json.loads(data["content_json"])
    except (json.JSONDecodeError, TypeError):
        data["content"] = data["content_json"]

    return data


def delete_material_by_id(material_id, custom_path=None):
    """Delete a saved material item by ID."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def save_quiz_result(title, subject, score, total_questions, time_spent_seconds=0, details=None, custom_path=None):
    """Record completed mock test score and breakdown."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    percentage = round((score / total_questions * 100), 1) if total_questions > 0 else 0.0
    details_str = json.dumps(details, ensure_ascii=False) if details else "{}"

    cursor.execute("""
        INSERT INTO quiz_results (title, subject, score, total_questions, percentage, time_spent_seconds, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title or "Mock Exam",
        subject or "General",
        score,
        total_questions,
        percentage,
        time_spent_seconds,
        details_str,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return result_id


def get_all_quiz_results(limit=20, custom_path=None):
    """Retrieve history of completed mock tests."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, subject, score, total_questions, percentage, time_spent_seconds, created_at
        FROM quiz_results ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_study_stats(custom_path=None):
    """Calculate actual study statistics for the dashboard."""
    conn = get_db_connection(custom_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM materials")
    total_materials = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT material_type, COUNT(*) as count
        FROM materials GROUP BY material_type
    """)
    type_counts = {row["material_type"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as total_quizzes, AVG(percentage) as avg_score FROM quiz_results")
    quiz_row = cursor.fetchone()
    total_quizzes = quiz_row["total_quizzes"] or 0
    avg_score = round(quiz_row["avg_score"] or 0.0, 1)

    conn.close()
    return {
        "total_materials": total_materials,
        "type_counts": type_counts,
        "total_quizzes": total_quizzes,
        "avg_score": avg_score
    }
