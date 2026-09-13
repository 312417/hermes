"""SQLite-backed local memory for Hermes."""

from __future__ import annotations

import os
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HermesStore:
    def __init__(self, data_dir: str | Path = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.data_dir.chmod(0o700)
        except OSError:
            pass
        self.db_path = self.data_dir / "hermes.sqlite3"
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    state TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS memories_chat_idx
                    ON memories(chat_id, id);
                CREATE TABLE IF NOT EXISTS pairing (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    chat_id INTEGER NOT NULL,
                    paired_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT
                );
                CREATE INDEX IF NOT EXISTS reminders_due_idx
                    ON reminders(delivered_at, due_at);
                """
            )
            task_columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)")}
            if "description" not in task_columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN description TEXT NOT NULL DEFAULT ''")
            self._migrate_json_if_needed(connection)
        try:
            self.db_path.chmod(0o600)
        except OSError:
            pass

    def _migrate_json_if_needed(self, connection: sqlite3.Connection) -> None:
        """Import the original JSON files once, preserving an existing install."""
        for table, filename, columns in (
            ("tasks", "tasks.json", ("id", "title", "created_at", "state")),
            ("knowledge", "knowledge.json", ("id", "title", "content", "created_at")),
        ):
            source = self.data_dir / filename
            if not source.exists() or connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
                continue
            try:
                import json

                rows = json.loads(source.read_text(encoding="utf-8"))
                for row in rows if isinstance(rows, list) else []:
                    values = [row.get(column, "") for column in columns]
                    placeholders = ",".join("?" for _ in columns)
                    connection.execute(
                        f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        values,
                    )
            except (OSError, ValueError, TypeError):
                continue

    def tasks(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, description, created_at, state FROM tasks ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_task(self, title: str, description: str = "") -> dict:
        task = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "description": description.strip(),
            "created_at": utc_now(),
            "state": "queued",
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO tasks (id, title, description, created_at, state) VALUES (?, ?, ?, ?, ?)",
                (task["id"], task["title"], task["description"], task["created_at"], task["state"]),
            )
        return task

    def complete_task(self, reference: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, description, created_at, state FROM tasks "
                "WHERE id = ? OR id LIKE ? ORDER BY rowid DESC LIMIT 1",
                (reference.strip(), f"{reference.strip()}%"),
            ).fetchone()
            if not row:
                return None
            connection.execute("UPDATE tasks SET state = 'done' WHERE id = ?", (row["id"],))
            result = dict(row)
            result["state"] = "done"
            return result

    def knowledge(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, content, created_at FROM knowledge ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]

    def teach(self, title: str, content: str) -> dict:
        entry = {"id": str(uuid.uuid4()), "title": title.strip(), "content": content.strip(), "created_at": utc_now()}
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO knowledge (id, title, content, created_at) VALUES (?, ?, ?, ?)",
                (entry["id"], entry["title"], entry["content"], entry["created_at"]),
            )
        return entry

    def remember_fact(self, title: str, content: str) -> dict:
        title = title.strip()
        content = content.strip()
        with self._connect() as connection:
            duplicate = connection.execute(
                "SELECT id, title, content, created_at FROM knowledge "
                "WHERE lower(title) = lower(?) AND lower(content) = lower(?) LIMIT 1",
                (title, content),
            ).fetchone()
            if duplicate:
                return dict(duplicate)
            if title.casefold() == "identidade":
                connection.execute("DELETE FROM knowledge WHERE lower(title) = 'identidade'")
            entry = {"id": str(uuid.uuid4()), "title": title, "content": content, "created_at": utc_now()}
            connection.execute(
                "INSERT INTO knowledge (id, title, content, created_at) VALUES (?, ?, ?, ?)",
                (entry["id"], entry["title"], entry["content"], entry["created_at"]),
            )
        return entry

    def search_knowledge(self, query: str) -> list[dict]:
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return []
        clauses = " OR ".join("(lower(title) LIKE ? OR lower(content) LIKE ?)" for _ in terms)
        parameters = [value for term in terms for value in (f"%{term}%", f"%{term}%")]
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT id, title, content, created_at FROM knowledge WHERE {clauses} ORDER BY rowid DESC LIMIT 5",
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def context_knowledge(self, query: str, limit: int = 12) -> list[dict]:
        permanent_titles = {"identidade", "perfil", "preferências", "projetos"}
        permanent = [entry for entry in self.knowledge() if entry["title"].casefold() in permanent_titles]
        combined: list[dict] = []
        seen: set[str] = set()
        for entry in [*permanent, *self.search_knowledge(query)]:
            if entry["id"] not in seen:
                seen.add(entry["id"])
                combined.append(entry)
        return combined[-limit:]

    def delete_knowledge(self, reference: str) -> dict | None:
        reference = reference.strip()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, content, created_at FROM knowledge "
                "WHERE id = ? OR id LIKE ? OR lower(title) = lower(?) "
                "ORDER BY rowid DESC LIMIT 1",
                (reference, f"{reference}%", reference),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM knowledge WHERE id = ?", (row["id"],))
        return dict(row)

    def add_memory(self, chat_id: int, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO memories (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, utc_now()),
            )
            limit = int(os.environ.get("HERMES_MEMORY_MESSAGES_PER_CHAT", "500"))
            connection.execute(
                "DELETE FROM memories WHERE chat_id = ? AND id NOT IN "
                "(SELECT id FROM memories WHERE chat_id = ? ORDER BY id DESC LIMIT ?)",
                (chat_id, chat_id, limit),
            )

    def recent_memories(self, chat_id: int, limit: int | None = None) -> list[dict]:
        active_limit = limit or int(os.environ.get("HERMES_ACTIVE_CONTEXT_MESSAGES", "24"))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role, content, created_at FROM memories WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, active_limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def clear_session(self, chat_id: int) -> int:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE chat_id = ?", (chat_id,))
        return int(cursor.rowcount)

    def add_reminder(self, chat_id: int, text: str, due_at: str) -> dict:
        reminder = {
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "text": text.strip(),
            "due_at": due_at,
            "created_at": utc_now(),
            "delivered_at": None,
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO reminders (id, chat_id, text, due_at, created_at, delivered_at) "
                "VALUES (?, ?, ?, ?, ?, NULL)",
                (reminder["id"], reminder["chat_id"], reminder["text"], reminder["due_at"], reminder["created_at"]),
            )
        return reminder

    def reminders(self, chat_id: int, pending_only: bool = True) -> list[dict]:
        where = "WHERE chat_id = ? AND delivered_at IS NULL" if pending_only else "WHERE chat_id = ?"
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT id, chat_id, text, due_at, created_at, delivered_at FROM reminders {where} ORDER BY due_at",
                (chat_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def due_reminders(self, now: str | None = None) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, chat_id, text, due_at, created_at, delivered_at FROM reminders "
                "WHERE delivered_at IS NULL AND due_at <= ? ORDER BY due_at LIMIT 20",
                (now or utc_now(),),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_reminder_delivered(self, reminder_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE reminders SET delivered_at = ? WHERE id = ? AND delivered_at IS NULL",
                (utc_now(), reminder_id),
            )

    def paired_chat_id(self) -> int | None:
        with self._connect() as connection:
            row = connection.execute("SELECT chat_id FROM pairing WHERE singleton = 1").fetchone()
        return int(row["chat_id"]) if row else None

    def pair_chat(self, chat_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO pairing (singleton, chat_id, paired_at) VALUES (1, ?, ?)",
                (chat_id, utc_now()),
            )


def default_store() -> HermesStore:
    return HermesStore(os.environ.get("HERMES_DATA_DIR", "./data"))
