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

PHONE_SSH_KEY="${PHONE_SSH_KEY:-$HOME/.ssh/id_phone}"
PHONE_HOST="${PHONE_HOST:-192.168.15.41}"
PHONE_USER="${PHONE_USER:-termux}"
PHONE_PORT="${PHONE_PORT:-8022}"
REMOTE="${PHONE_USER}@${PHONE_HOST}"
SSH_OPTS=(-p "$PHONE_PORT" -i "$PHONE_SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10)
SCP_OPTS=(-P "$PHONE_PORT" -i "$PHONE_SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10)

echo "==> Verificando conexão com $REMOTE:$PHONE_PORT"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'echo "Conectado: $(uname -m) $(date)"'

echo "==> Parando processos legados anteriores se existirem"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'pkill -f "[p]ython3.*(server\.py|telegram_bot\.py|supervisor\.py)" 2>/dev/null || true'

echo "==> Verificando se o Hermes oficial está instalado no container Ubuntu"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'proot-distro login ubuntu -- bash -lc "
  command -v hermes >/dev/null || {
    echo \"Instalando Hermes no Ubuntu...\";
    git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /root/hermes-agent 2>/dev/null || (cd /root/hermes-agent && git pull);
    cd /root/hermes-agent;
    /root/.hermes/bin/uv venv /root/hermes-agent/venv --python 3.11;
    /root/.hermes/bin/uv pip install -e . --python /root/hermes-agent/venv/bin/python;
    ln -sf /root/hermes-agent/venv/bin/hermes /usr/local/bin/hermes;
  }
"'

echo "==> Criando diretórios no celular e no container"
ssh "${SSH_OPTS[@]}" "$REMOTE" '
  mkdir -p ~/.hermes/profile ~/.hermes/skills ~/.termux/boot
  proot-distro login ubuntu -- bash -c "mkdir -p /root/.hermes/profile /root/.hermes/skills"
'

echo "==> Enviando configuração e perfis"
scp "${SCP_OPTS[@]}" profile/* "$REMOTE:~/.hermes/profile/"
scp "${SCP_OPTS[@]}" config/config.template.yaml "$REMOTE:~/.hermes/config.template.yaml"
if [ -d skills ]; then
  scp -r "${SCP_OPTS[@]}" skills "$REMOTE:~/.hermes/" || true
fi

ssh "${SSH_OPTS[@]}" "$REMOTE" 'proot-distro login ubuntu -- bash -c "
  cp -r /data/data/com.termux/files/home/.hermes/profile/* /root/.hermes/profile/
  cp /data/data/com.termux/files/home/.hermes/config.template.yaml /root/.hermes/config.template.yaml
"'

echo "==> Instalando script de boot"
scp "${SCP_OPTS[@]}" deploy/start-hermes "$REMOTE:~/start-hermes"
ssh "${SSH_OPTS[@]}" "$REMOTE" \
  'install -m 700 ~/start-hermes ~/.termux/boot/20-hermes; rm -f ~/start-hermes'

echo "==> Reiniciando gateway"
ssh "${SSH_OPTS[@]}" "$REMOTE" 'pkill -f "[2]0-hermes" 2>/dev/null || true; pkill -f "[h]ermes gateway" 2>/dev/null || true'
ssh "${SSH_OPTS[@]}" "$REMOTE" "nohup ~/.termux/boot/20-hermes </dev/null >/dev/null 2>&1 &" || true

echo "==> Aguardando inicialização (5s)"
sleep 5

echo "==> Executando diagnóstico"
bash deploy/health-phone.sh

echo "Deploy concluído com sucesso."
