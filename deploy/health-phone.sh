#!/usr/bin/env bash
# health-phone.sh — Valida se o Hermes Agent está saudável no celular.
#
# Uso:
#   PHONE_SSH_KEY=~/.ssh/phone PHONE_HOST=192.168.x.x PHONE_USER=u0_a123 ./deploy/health-phone.sh
set -euo pipefail

: "${PHONE_SSH_KEY:?Set PHONE_SSH_KEY to the private SSH key path}"
: "${PHONE_HOST:?Set PHONE_HOST to the phone IP or hostname}"
: "${PHONE_USER:?Set PHONE_USER to the Termux SSH user}"
PHONE_PORT="${PHONE_PORT:-8022}"
REMOTE="${PHONE_USER}@${PHONE_HOST}"
SSH_OPTS=(-p "$PHONE_PORT" -i "$PHONE_SSH_KEY" -o ConnectTimeout=10)

echo "==> Verificando processo do gateway"
if ssh "${SSH_OPTS[@]}" "$REMOTE" 'pgrep -f "hermes gateway" >/dev/null'; then
  echo "    ✅ Gateway Telegram rodando"
else
  echo "    ❌ Gateway Telegram NÃO encontrado"
  exit 1
fi

echo "==> Verificando instalação do Hermes"
HERMES_VERSION=$(ssh "${SSH_OPTS[@]}" "$REMOTE" 'hermes --version 2>/dev/null || echo "não encontrado"')
echo "    Versão: $HERMES_VERSION"

echo "==> Verificando arquivos de identidade"
for file in profile/SOUL.md profile/AGENTS.md; do
  if ssh "${SSH_OPTS[@]}" "$REMOTE" "test -f ~/.hermes/$file"; then
    echo "    ✅ ~/.hermes/$file"
  else
    echo "    ❌ ~/.hermes/$file ausente"
  fi
done

echo "==> Verificando segredos (existência, não conteúdo)"
if ssh "${SSH_OPTS[@]}" "$REMOTE" 'test -f ~/.hermes/.env'; then
  echo "    ✅ ~/.hermes/.env existe"
  PERMS=$(ssh "${SSH_OPTS[@]}" "$REMOTE" 'stat -c "%a" ~/.hermes/.env 2>/dev/null || stat -f "%Lp" ~/.hermes/.env 2>/dev/null')
  if [ "$PERMS" = "600" ]; then
    echo "    ✅ Permissões corretas (600)"
  else
    echo "    ⚠️  Permissões: $PERMS (esperado: 600)"
  fi
else
  echo "    ❌ ~/.hermes/.env ausente — configure antes de usar"
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
