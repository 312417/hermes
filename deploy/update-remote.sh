#!/usr/bin/env bash
# update-remote.sh — Atualiza o Hermes diretamente a partir do repositório GitHub.
# Pode ser executado dentro do container Ubuntu no celular a qualquer momento.

set -euo pipefail

REPO_DIR="/root/hermes-repo"
HERMES_DIR="/root/.hermes"

echo "==> Sincronizando com o GitHub (312417/hermes)..."
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone https://github.com/312417/hermes.git "$REPO_DIR"
fi

cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main

COMMIT_INFO=$(git log -1 --format="%h — %s (%cd)" --date=short)

echo "==> Atualizando perfis e identidade..."
mkdir -p "$HERMES_DIR/profile" "$HERMES_DIR/skills"
cp -r profile/* "$HERMES_DIR/profile/"
cp profile/SOUL.md "$HERMES_DIR/SOUL.md"

echo "==> Atualizando skills..."
if [ -d skills ]; then
  cp -r skills/* "$HERMES_DIR/skills/"
fi

echo "==> Atualizando configuração..."
cp config/config.template.yaml "$HERMES_DIR/config.yaml"

echo "==> Concluído com sucesso: $COMMIT_INFO"

# Reinicia o gateway se solicitado
if [ "${1:-}" = "--restart" ]; then
  echo "==> Reiniciando gateway em 2 segundos..."
  (sleep 2 && pkill -f "hermes gateway run") &
fi
