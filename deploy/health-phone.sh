#!/usr/bin/env bash
# health-phone.sh — Valida se o Hermes Agent está saudável no celular.
#
# Uso:
#   PHONE_SSH_KEY=~/.ssh/phone PHONE_HOST=192.168.x.x PHONE_USER=u0_a123 ./deploy/health-phone.sh
set -euo pipefail

PHONE_SSH_KEY="${PHONE_SSH_KEY:-$HOME/.ssh/id_phone}"
PHONE_HOST="${PHONE_HOST:-192.168.15.41}"
PHONE_USER="${PHONE_USER:-termux}"
PHONE_PORT="${PHONE_PORT:-8022}"
REMOTE="${PHONE_USER}@${PHONE_HOST}"
SSH_OPTS=(-p "$PHONE_PORT" -i "$PHONE_SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10)

echo "==> Verificando processo do gateway"
if ssh "${SSH_OPTS[@]}" "$REMOTE" 'pgrep -f "[h]ermes gateway" >/dev/null || pgrep -f "[2]0-hermes" >/dev/null'; then
  echo "    ✅ Processo do Gateway Telegram ativo"
else
  echo "    ⚠️ Gateway Telegram ainda não ativo"
fi

echo "==> Verificando instalação do Hermes"
HERMES_VERSION=$(ssh "${SSH_OPTS[@]}" "$REMOTE" 'proot-distro login ubuntu -- bash -lc "hermes --version 2>/dev/null" || echo "não encontrado"')
echo "    Versão: $HERMES_VERSION"

echo "==> Verificando arquivos de identidade"
for file in profile/SOUL.md profile/AGENTS.md; do
  if ssh "${SSH_OPTS[@]}" "$REMOTE" "proot-distro login ubuntu -- test -f /root/.hermes/$file"; then
    echo "    ✅ /root/.hermes/$file"
  else
    echo "    ❌ /root/.hermes/$file ausente"
  fi
done

echo "==> Verificando segredos (existência, não conteúdo)"
if ssh "${SSH_OPTS[@]}" "$REMOTE" 'proot-distro login ubuntu -- test -f /root/.hermes/.env || test -f ~/.hermes/.env'; then
  echo "    ✅ ~/.hermes/.env ou /root/.hermes/.env configurado"
else
  echo "    ⚠️ ~/.hermes/.env ausente — configure suas chaves de API"
fi

echo "==> Verificando Termux:Boot"
if ssh "${SSH_OPTS[@]}" "$REMOTE" 'test -x ~/.termux/boot/20-hermes'; then
  echo "    ✅ Script de boot instalado"
else
  echo "    ❌ Script de boot ausente"
fi

echo "==> Últimas linhas do log do gateway"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'tail -5 ~/hermes-gateway.log 2>/dev/null || echo "(sem log ainda)"'

echo ""
echo "Diagnóstico concluído."
