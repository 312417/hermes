#!/usr/bin/env bash
set -euo pipefail

: "${PHONE_SSH_KEY:?Set PHONE_SSH_KEY to the private SSH key path}"
: "${PHONE_HOST:?Set PHONE_HOST to the phone IP or hostname}"
: "${PHONE_USER:?Set PHONE_USER to the Termux SSH user}"
PHONE_PORT="${PHONE_PORT:-8022}"
REMOTE="${PHONE_USER}@${PHONE_HOST}"

scp -P "$PHONE_PORT" -i "$PHONE_SSH_KEY" \
  server.py hermes_store.py tool_registry.py model_provider.py natural_language.py telegram_bot.py supervisor.py \
  configure-secrets.sh README.md telegram.env.example deploy/start-hermes "$REMOTE:"

ssh -p "$PHONE_PORT" -i "$PHONE_SSH_KEY" "$REMOTE" \
  'mkdir -p ~/.termux/boot; install -m 700 start-hermes ~/.termux/boot/20-hermes; \
   proot-distro login ubuntu --bind /data/data/com.termux/files/home:/mnt/termux-home \
   -- bash -lc "install -d -o hermes -g hermes /home/hermes/hermes-agent; \
   for file in server.py hermes_store.py tool_registry.py model_provider.py natural_language.py telegram_bot.py supervisor.py configure-secrets.sh README.md telegram.env.example; do \
     install -o hermes -g hermes -m 0644 /mnt/termux-home/\$file /home/hermes/hermes-agent/\$file; \
   done; \
   chmod 0700 /home/hermes/hermes-agent/configure-secrets.sh; \
   pkill -f \"python3 (server.py|telegram_bot.py|supervisor.py)\" || true"; \
   nohup ~/.termux/boot/20-hermes >/dev/null 2>&1 &'

echo "Hermes deployed to $REMOTE:$PHONE_PORT"
