#!/usr/bin/env bash
set -euo pipefail

config_dir="${HERMES_CONFIG_DIR:-$HOME/.config/hermes}"
config_file="$config_dir/telegram.env"
mkdir -p "$config_dir"
umask 077

printf 'Token do bot criado no @BotFather: '
read -r telegram_token
printf 'Chave da API OpenAI: '
read -r -s openai_key
printf '\nModelo OpenAI [gpt-5.6-luna]: '
read -r openai_model
openai_model="${openai_model:-gpt-5.6-luna}"
pairing_code="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

{
  printf 'TELEGRAM_BOT_TOKEN=%s\n' "$telegram_token"
  printf 'TELEGRAM_PAIRING_CODE=%s\n' "$pairing_code"
  printf 'TELEGRAM_ALLOWED_CHAT_IDS=\n'
  printf 'HERMES_MODEL_PROVIDER=openai\n'
  printf 'OPENAI_MODEL=%s\n' "$openai_model"
  printf 'OPENAI_API_KEY=%s\n' "$openai_key"
} > "$config_file"
chmod 600 "$config_file"

printf '\nConfiguração salva em %s\n' "$config_file"
printf 'Código de pareamento: %s\n' "$pairing_code"
printf 'Envie /pair %s ao bot no Telegram.\n' "$pairing_code"
