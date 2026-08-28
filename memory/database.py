import re
import sqlite3
from pathlib import Path
import sqlite3
from datetime import datetime



PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "vyra.db"


def initialize_database() -> None:
    """Create the VYRA database tables if they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    try:
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
                status TEXT NOT NULL DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT,
                completed_at TEXT,
                missed_at TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS briefing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                briefing_date TEXT NOT NULL,
                topics TEXT NOT NULL,
                summary TEXT,
                delivered_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS important_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                place_type TEXT NOT NULL,
                city TEXT,
                region TEXT,
                country TEXT,
                importance INTEGER NOT NULL DEFAULT 50,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intelligence_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_type TEXT NOT NULL,
                story_category TEXT,
                entity_names TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intelligence_discovery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_identity TEXT NOT NULL UNIQUE,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intelligence_delivery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_identity TEXT NOT NULL,
                title TEXT,
                category TEXT,
                source TEXT,
                url TEXT,
                delivered_at TIMESTAMP NOT NULL,
                delivery_type TEXT NOT NULL,
                priority TEXT
            )
            """
        )

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_intel_delivery_delivered_at ON intelligence_delivery_history(delivered_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_intel_delivery_category ON intelligence_delivery_history(category)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_intel_delivery_source ON intelligence_delivery_history(source)"
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interaction_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()
    finally:
        connection.close()

    migrate_tasks_table()

def migrate_tasks_table() -> None:
    """Add new task columns to an existing VYRA database."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            "PRAGMA table_info(tasks)"
        )

        existing_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        required_columns = {
            "delivered_at": "TEXT",
            "completed_at": "TEXT",
            "missed_at": "TEXT",
        }

        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE tasks ADD COLUMN "
                    f"{column_name} {column_type}"
                )

        connection.commit()
    finally:
        connection.close()

def save_memory(memory_type: str, content: str) -> None:
    """Save a long-term memory."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO memories (memory_type, content)
            VALUES (?, ?)
            """,
            (memory_type, content),
        )

        connection.commit()
    finally:
        connection.close()


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
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT memory_type, content
            FROM memories
            ORDER BY id ASC
            """
        )

        memories = cursor.fetchall()
    finally:
        connection.close()

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
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO tasks (title, due_at)
            VALUES (?, ?)
            """,
            (title, due_at),
        )

        connection.commit()
    finally:
        connection.close()


def get_pending_tasks() -> list[tuple]:
    """Return active tasks with their full reminder state."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                title,
                due_at,
                status,
                created_at,
                delivered_at,
                completed_at,
                missed_at
            FROM tasks
            WHERE status IN (
                'scheduled',
                'pending',
                'due',
                'missed'
            )
            ORDER BY
                CASE
                    WHEN due_at IS NULL THEN 1
                    ELSE 0
                END,
                due_at ASC
            """
        )

        return cursor.fetchall()
    finally:
        connection.close()


def complete_task(task_id: int) -> None:
    """Mark a task as completed."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ?
            """,
            (task_id,),
        )

        connection.commit()
    finally:
        connection.close()

def delete_task(task_id: int) -> None:
    """Delete a task by its ID."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            DELETE FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        )

        connection.commit()
    finally:
        connection.close()

def mark_task_due(task_id: int) -> None:
    """Mark a scheduled task as due."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'due'
            WHERE id = ?
            AND status IN ('scheduled', 'pending')
            """,
            (task_id,),
        )

        connection.commit()
    finally:
        connection.close()


def mark_task_delivered(task_id: int) -> None:
    """Mark a task reminder as delivered."""

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'delivered',
                delivered_at = ?
            WHERE id = ?
            """,
            (now, task_id),
        )

        connection.commit()
    finally:
        connection.close()


def mark_task_missed(task_id: int) -> None:
    """Mark a task reminder as missed."""

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'missed',
                missed_at = ?
            WHERE id = ?
            """,
            (now, task_id),
        )

        connection.commit()
    finally:
        connection.close()


def complete_task(task_id: int) -> None:
    """Mark a task as completed."""

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'completed',
                completed_at = ?
            WHERE id = ?
            """,
            (now, task_id),
        )

        connection.commit()
    finally:
        connection.close()

def get_missed_tasks() -> list[tuple]:
    """Return tasks that were missed and have not been handled yet."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                title,
                due_at,
                status,
                created_at,
                delivered_at,
                completed_at,
                missed_at
            FROM tasks
            WHERE status = 'missed'
            ORDER BY missed_at ASC
            """
        )

        return cursor.fetchall()
    finally:
        connection.close()

def acknowledge_missed_task(task_id: int) -> None:
    """Mark a missed reminder as acknowledged by the user."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'acknowledged'
            WHERE id = ?
            AND status = 'missed'
            """,
            (task_id,),
        )

        connection.commit()
    finally:
        connection.close()

def save_briefing_history(
    briefing_date: str,
    topics: list[str],
    summary: str,
    delivered_at: str,
) -> None:
    """Save lightweight history about a delivered briefing."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO briefing_history (
                briefing_date,
                topics,
                summary,
                delivered_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                briefing_date,
                ", ".join(topics),
                summary,
                delivered_at,
            ),
        )

        connection.commit()
    finally:
        connection.close()

def get_recent_briefing_history(
    limit: int = 7,
) -> list[tuple]:
    """Return recent briefing history entries."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                briefing_date,
                topics,
                summary,
                delivered_at
            FROM briefing_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return cursor.fetchall()
    finally:
        connection.close()

def get_today_briefing_history(
    briefing_date: str,
) -> list[tuple]:
    """Return today's briefing history."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                briefing_date,
                topics,
                summary,
                delivered_at
            FROM briefing_history
            WHERE briefing_date = ?
            ORDER BY id DESC
            """,
            (briefing_date,),
        )

        return cursor.fetchall()
    finally:
        connection.close()

def save_important_place(
    name: str,
    place_type: str,
    city: str | None = None,
    region: str | None = None,
    country: str | None = None,
    importance: int = 50,
    notes: str | None = None,
) -> None:
    """Save a personally important place."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO important_places (
                name,
                place_type,
                city,
                region,
                country,
                importance,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                place_type,
                city,
                region,
                country,
                importance,
                notes,
            ),
        )

        connection.commit()
    finally:
        connection.close()


def get_important_places() -> list[tuple]:
    """Return all personally important places."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                name,
                place_type,
                city,
                region,
                country,
                importance,
                notes,
                created_at
            FROM important_places
            ORDER BY importance DESC, id ASC
            """
        )

        return cursor.fetchall()
    finally:
        connection.close()

def save_intelligence_feedback(
    feedback_type: str,
    story_category: str | None = None,
    entity_names: tuple[str, ...] = (),
    source: str | None = None,
) -> None:
    """Persist one intelligence feedback event."""

    entities_text = ",".join(entity_names)

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO intelligence_feedback (
                feedback_type,
                story_category,
                entity_names,
                source
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                feedback_type,
                story_category,
                entities_text,
                source,
            ),
        )

        connection.commit()
    finally:
        connection.close()


def get_intelligence_feedback() -> list[tuple]:
    """Return all persisted intelligence feedback."""

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                feedback_type,
                story_category,
                entity_names,
                source,
                created_at
            FROM intelligence_feedback
            ORDER BY id ASC
            """
        )

        return cursor.fetchall()
    finally:
        connection.close()

def clear_intelligence_feedback() -> None:
    """Delete all intelligence feedback.

    Intended for tests/development cleanup.
    """

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            "DELETE FROM intelligence_feedback"
        )

        connection.commit()
    finally:
        connection.close()

def save_intelligence_discovery(
    story_identity: str,
) -> None:
    """Persist that an intelligence discovery was delivered."""

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        connection.execute(
            """
            INSERT OR IGNORE INTO intelligence_discovery_history (
                story_identity
            )
            VALUES (?)
            """,
            (story_identity,),
        )

        connection.commit()

    finally:
        connection.close()


def get_intelligence_discovery_history() -> list[str]:
    """Return all persisted discovery identities."""

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        cursor = connection.execute(
            """
            SELECT story_identity
            FROM intelligence_discovery_history
            ORDER BY id ASC
            """
        )

        return [
            row[0]
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def clear_intelligence_discovery_history() -> None:
    """Clear persisted discovery history."""

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        connection.execute(
            "DELETE FROM intelligence_discovery_history"
        )

        connection.commit()

    finally:
        connection.close()


def save_intelligence_delivery(
    story_identity: str,
    title: str | None,
    category: str | None,
    source: str | None,
    url: str | None,
    delivered_at,
    delivery_type: str,
    priority: str | None = None,
) -> None:
    """Persist an actual intelligence delivery."""

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute(
            """
            INSERT INTO intelligence_delivery_history (
                story_identity,
                title,
                category,
                source,
                url,
                delivered_at,
                delivery_type,
                priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                story_identity,
                title,
                category,
                source,
                url,
                delivered_at,
                delivery_type,
                priority,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_intelligence_delivery_history(limit: int = 100) -> list[tuple]:
    """Return recent intelligence deliveries newest first."""

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.execute(
            """
            SELECT id, story_identity, title, category, source, url, delivered_at, delivery_type, priority
            FROM intelligence_delivery_history
            ORDER BY delivered_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()
    finally:
        connection.close()


def clear_intelligence_delivery_history() -> None:
    """Clear persisted delivery history for testing."""

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("DELETE FROM intelligence_delivery_history")
        connection.commit()
    finally:
        connection.close()


def load_interaction_state(key: str) -> str | None:
    """Load a persisted interaction state value."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            "SELECT value FROM interaction_state WHERE key = ?",
            (key,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        connection.close()


def save_interaction_state(key: str, value: str) -> None:
    """Save an interaction state value."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            "INSERT INTO interaction_state(key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, value),
        )
        connection.commit()
    finally:
        connection.close()