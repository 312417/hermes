#!/usr/bin/env python3
"""Hermes: a small local control service designed for a Termux host."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hermes_store import default_store


HOST = os.environ.get("HERMES_HOST", "127.0.0.1")
PORT = int(os.environ.get("HERMES_PORT", "8787"))
STORE = default_store()
STARTED_AT = datetime.now(timezone.utc).isoformat()
START_MONOTONIC = time.monotonic()


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
                    "tasks": len(STORE.tasks()),
                },
            )
        elif self.path == "/tasks":
            self.reply(HTTPStatus.OK, {"tasks": STORE.tasks()})
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

        task = STORE.add_task(title)
        self.reply(HTTPStatus.CREATED, task)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), HermesHandler)
    print(f"Hermes listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
