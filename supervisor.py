#!/usr/bin/env python3
"""Run the local HTTP service and Telegram transport together."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def load_env() -> None:
    env_path = Path(os.environ.get("HERMES_ENV_FILE", "/home/hermes/.config/hermes/telegram.env"))
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    load_env()
    processes = [subprocess.Popen([sys.executable, "server.py"])]
    if os.environ.get("TELEGRAM_BOT_TOKEN", "").strip():
        processes.append(subprocess.Popen([sys.executable, "telegram_bot.py"]))
    else:
        print("Telegram transport disabled: configure TELEGRAM_BOT_TOKEN", flush=True)

    def stop(_signal: int, _frame: object) -> None:
        for process in processes:
            process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise SystemExit(f"child exited with status {process.returncode}")
            time.sleep(2)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    main()
