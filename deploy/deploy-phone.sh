#!/usr/bin/env bash
# deploy-phone.sh — Atualiza configuração e reinicia o Hermes Agent no celular.
#
# Uso:
#   PHONE_SSH_KEY=~/.ssh/phone PHONE_HOST=192.168.x.x PHONE_USER=u0_a123 ./deploy/deploy-phone.sh
#
# Requisitos no celular:
#   - Hermes Agent oficial instalado (curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash)
#   - ~/.hermes/.env com segredos configurados
#   - Termux:Boot instalado
set -euo pipefail

: "${PHONE_SSH_KEY:?Set PHONE_SSH_KEY to the private SSH key path}"
: "${PHONE_HOST:?Set PHONE_HOST to the phone IP or hostname}"
: "${PHONE_USER:?Set PHONE_USER to the Termux SSH user}"
PHONE_PORT="${PHONE_PORT:-8022}"
REMOTE="${PHONE_USER}@${PHONE_HOST}"
SSH_OPTS=(-p "$PHONE_PORT" -i "$PHONE_SSH_KEY" -o ConnectTimeout=10)

echo "==> Verificando conexão com $REMOTE:$PHONE_PORT"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'echo "Conectado: $(uname -m) $(date)"'

echo "==> Verificando se o Hermes oficial está instalado"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'command -v hermes >/dev/null || {
  echo "Hermes não encontrado. Instalando...";
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash;
  source ~/.bashrc;
}'

echo "==> Enviando configuração e scripts"
rsync -avz --delete -e "ssh ${SSH_OPTS[*]}" \
  profile/ "$REMOTE:~/.hermes/profile/"

rsync -avz -e "ssh ${SSH_OPTS[*]}" \
  config/config.template.yaml "$REMOTE:~/.hermes/config.template.yaml"

rsync -avz -e "ssh ${SSH_OPTS[*]}" \
  skills/ "$REMOTE:~/.hermes/skills/"

echo "==> Instalando script de boot"
scp "${SSH_OPTS[@]}" deploy/start-hermes "$REMOTE:~/start-hermes"
ssh "${SSH_OPTS[@]}" "$REMOTE" \
  'mkdir -p ~/.termux/boot; install -m 700 ~/start-hermes ~/.termux/boot/20-hermes; rm ~/start-hermes'

echo "==> Reiniciando gateway"
ssh "${SSH_OPTS[@]}" "$REMOTE" \
  'pkill -f "hermes gateway" || true; sleep 2; nohup ~/.termux/boot/20-hermes >/dev/null 2>&1 &'

echo "==> Aguardando inicialização (5s)"
sleep 5

echo "==> Executando diagnóstico"
bash deploy/health-phone.sh

echo "Deploy concluído com sucesso."
