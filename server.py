#!/usr/bin/env python3
"""Hermes: a small local control service designed for a Termux host."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.environ.get("HERMES_HOST", "127.0.0.1")
PORT = int(os.environ.get("HERMES_PORT", "8787"))
DATA_DIR = Path(os.environ.get("HERMES_DATA_DIR", "./data"))
TASKS_PATH = DATA_DIR / "tasks.json"
STARTED_AT = datetime.now(timezone.utc).isoformat()
START_MONOTONIC = time.monotonic()


def load_tasks() -> list[dict]:
    if not TASKS_PATH.exists():
        return []
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))


def save_tasks(tasks: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = TASKS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    temporary.replace(TASKS_PATH)


class HermesHandler(BaseHTTPRequestHandler):
    server_version = "Hermes/0.1"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {format % args}")

    def reply(self, status: HTTPStatus, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.reply(HTTPStatus.OK, {"ok": True, "service": "hermes"})
        elif self.path == "/status":
            self.reply(
                HTTPStatus.OK,
                {
                    "service": "hermes",
                    "started_at": STARTED_AT,
                    "uptime_seconds": round(time.monotonic() - START_MONOTONIC, 2),
                    "tasks": len(load_tasks()),
                },
            )
        elif self.path == "/tasks":
            self.reply(HTTPStatus.OK, {"tasks": load_tasks()})
        else:
            self.reply(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/tasks":
            self.reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            title = str(request["title"]).strip()
            if not title:
                raise ValueError("title cannot be empty")
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            self.reply(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        tasks = load_tasks()
        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": "queued",
        }
        tasks.append(task)
        save_tasks(tasks)
        self.reply(HTTPStatus.CREATED, task)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), HermesHandler)
    print(f"Hermes listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
