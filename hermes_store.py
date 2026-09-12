"""Small file-backed storage shared by the HTTP and Telegram interfaces."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HermesStore:
    def __init__(self, data_dir: str | Path = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.tasks_path = self.data_dir / "tasks.json"
        self.knowledge_path = self.data_dir / "knowledge.json"
        self.pairing_path = self.data_dir / "telegram_pairing.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.data_dir.chmod(0o700)
        except OSError:
            pass

    def _read_list(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    def _write(self, path: Path, value: object) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def tasks(self) -> list[dict]:
        return self._read_list(self.tasks_path)

    def add_task(self, title: str) -> dict:
        task = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "created_at": utc_now(),
            "state": "queued",
        }
        tasks = self.tasks()
        tasks.append(task)
        self._write(self.tasks_path, tasks)
        return task

    def knowledge(self) -> list[dict]:
        return self._read_list(self.knowledge_path)

    def teach(self, title: str, content: str) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "content": content.strip(),
            "created_at": utc_now(),
        }
        entries = self.knowledge()
        entries.append(entry)
        self._write(self.knowledge_path, entries)
        return entry

    def search_knowledge(self, query: str) -> list[dict]:
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return []
        results = []
        for entry in self.knowledge():
            haystack = f"{entry.get('title', '')} {entry.get('content', '')}".lower()
            if all(term in haystack for term in terms):
                results.append(entry)
        return results[:5]

    def paired_chat_id(self) -> int | None:
        if not self.pairing_path.exists():
            return None
        try:
            value = json.loads(self.pairing_path.read_text(encoding="utf-8"))
            return int(value["chat_id"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def pair_chat(self, chat_id: int) -> None:
        self._write(self.pairing_path, {"chat_id": chat_id, "paired_at": utc_now()})


def default_store() -> HermesStore:
    return HermesStore(os.environ.get("HERMES_DATA_DIR", "./data"))
