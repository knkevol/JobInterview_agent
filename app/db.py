import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "interview_agent.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_connection()
    # 테이블 생성
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                explanation TEXT,
                difficulty INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL REFERENCES quiz_bank(id),
                session_id TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                answered_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                status TEXT NOT NULL,
                knowledge_base_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL
                )        
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL REFERENCES repositories(id),
                created_at TEXT NOT NULL
            )
        """)
        # 꼬리질문. 자기참조테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id),
                parent_question_id TEXT REFERENCES questions(id),
                depth INTEGER NOT NULL DEFAULT 0,
                question_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL REFERENCES questions(id),
                answer_text TEXT NOT NULL,
                evaluation_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")