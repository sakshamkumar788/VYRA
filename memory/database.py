import re
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "vyra.db"


def initialize_database() -> None:
    """Create the VYRA database and memory table if they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_memory(memory_type: str, content: str) -> None:
    """Save a long-term memory."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO memories (memory_type, content)
            VALUES (?, ?)
            """,
            (memory_type, content),
        )

        connection.commit()


def tokenize(text: str) -> set[str]:
    """
    Convert text into normalized words.

    Punctuation is removed, so:
        'learning?'
    becomes:
        'learning'
    """
    return {
        word.lower()
        for word in re.findall(r"\b\w+\b", text)
        if len(word) >= 3
    }


def get_relevant_memories(query: str) -> list[tuple[str, str]]:
    """
    Return memories containing words relevant to the query.

    This is intentionally a simple first version.
    We will replace it with semantic retrieval later.
    """
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            SELECT memory_type, content
            FROM memories
            ORDER BY id ASC
            """
        )

        memories = cursor.fetchall()

    query_words = tokenize(query)

    relevant_memories: list[tuple[str, str]] = []

    for memory_type, content in memories:
        content_words = tokenize(content)

        if query_words & content_words:
            relevant_memories.append(
                (memory_type, content)
            )

    return relevant_memories

def save_task(title: str, due_at: str | None = None) -> None:
    """Save a new task."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO tasks (title, due_at)
            VALUES (?, ?)
            """,
            (title, due_at),
        )

        connection.commit()


def get_pending_tasks() -> list[tuple[int, str, str | None, str]]:
    """Return all pending tasks."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            SELECT id, title, due_at, status
            FROM tasks
            WHERE status = 'pending'
            ORDER BY id ASC
            """
        )

        return cursor.fetchall()


def complete_task(task_id: int) -> None:
    """Mark a task as completed."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ?
            """,
            (task_id,),
        )

        connection.commit()