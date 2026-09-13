#!/usr/bin/env python3
"""Non-sensitive runtime validation for a deployed Hermes instance."""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing

from hermes_store import default_store
from model_provider import provider_from_env
from supervisor import load_env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-model", action="store_true")
    args = parser.parse_args()

    load_env()
    store = default_store()
    with closing(sqlite3.connect(store.db_path)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    required = {"tasks", "knowledge", "memories", "reminders", "pairing"}
    print(f"schema-ok={required.issubset(tables)}")
    print(f"session-messages={sum(1 for _ in store.recent_memories(store.paired_chat_id() or 0, limit=500))}")
    print(f"knowledge-items={len(store.knowledge())}")
    print(f"pending-reminders={len(store.reminders(store.paired_chat_id() or 0))}")
    print(f"paired={store.paired_chat_id() is not None}")

    if args.live_model:
        provider = provider_from_env()
        if provider is None:
            raise SystemExit("model-configured=False")
        answer = provider.respond(
            [{"role": "user", "content": "Responda exatamente: modelo-ok"}],
            [],
            prompt="#fast Responda exatamente: modelo-ok",
        )
        print(f"model-answer={answer}")


if __name__ == "__main__":
    main()
