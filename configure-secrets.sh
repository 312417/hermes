#!/usr/bin/env bash
set -euo pipefail

config_dir="${HERMES_CONFIG_DIR:-$HOME/.config/hermes}"
config_file="$config_dir/telegram.env"
mkdir -p "$config_dir"
umask 077

printf 'Token do bot criado no @BotFather: '
read -r telegram_token
printf 'Chave da API Groq: '
read -r -s groq_key
pairing_code="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

{
  printf 'TELEGRAM_BOT_TOKEN=%s\n' "$telegram_token"
  printf 'TELEGRAM_PAIRING_CODE=%s\n' "$pairing_code"
  printf 'TELEGRAM_ALLOWED_CHAT_IDS=\n'
  printf 'HERMES_TIMEZONE=America/Sao_Paulo\n'
  printf 'HERMES_ACTIVE_CONTEXT_MESSAGES=24\n'
  printf 'HERMES_MEMORY_MESSAGES_PER_CHAT=500\n'
  printf 'HERMES_MODEL_PROVIDER=groq\n'
  printf 'GROQ_API_KEY=%s\n' "$groq_key"
  printf 'HERMES_FAST_MODEL=openai/gpt-oss-20b\n'
  printf 'HERMES_TEXT_MODEL=llama-3.3-70b-versatile\n'
  printf 'HERMES_THINK_MODEL=openai/gpt-oss-120b\n'
  printf 'HERMES_RESEARCH_MODEL=groq/compound\n'
} > "$config_file"
chmod 600 "$config_file"

printf '\nConfiguração salva em %s\n' "$config_file"
printf 'Código de pareamento: %s\n' "$pairing_code"
printf 'Envie /pair %s ao bot no Telegram.\n' "$pairing_code"
