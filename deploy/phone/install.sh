#!/data/data/com.termux/files/usr/bin/sh
# install.sh — Idempotent installer for Hermes high-availability stack on Samsung S20 FE
set -eu

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME="${HOME:-/data/data/com.termux/files/home}"
OPS_DIR="$HOME/.hermes-ops"
SVDIR="$PREFIX/var/service"
BOOT_DIR="$HOME/.termux/boot"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> 1. Criando diretórios operacionais em ~/.hermes-ops"
mkdir -p "$OPS_DIR/bin" "$OPS_DIR/state" "$OPS_DIR/logs" "$OPS_DIR/legacy" "$BOOT_DIR" "$PREFIX/var/log"

echo "==> 2. Preservando scripts legados em ~/.hermes-ops/legacy/"
for f in "$BOOT_DIR/20-hermes" "$BOOT_DIR/start-server" "$HOME/watchdog-hermes.sh" "$HOME/start-tunnel.sh"; do
  if [ -f "$f" ]; then
    cp "$f" "$OPS_DIR/legacy/"
    echo "    Arquivado: $f -> $OPS_DIR/legacy/$(basename "$f")"
  fi
done

echo "==> 3. Instalando ferramentas em ~/.hermes-ops/bin/"
cp "$SRC_DIR/bin/hermes-health" "$OPS_DIR/bin/hermes-health"
cp "$SRC_DIR/bin/hermes-recover" "$OPS_DIR/bin/hermes-recover"
cp "$SRC_DIR/bin/hermes-backup" "$OPS_DIR/bin/hermes-backup"
chmod 755 "$OPS_DIR/bin/hermes-health" "$OPS_DIR/bin/hermes-recover" "$OPS_DIR/bin/hermes-backup"

echo "==> 4. Instalando comando unificado 'hermes' em $PREFIX/bin/hermes"
rm -f "$PREFIX/bin/hermes" 2>/dev/null || true
cp "$SRC_DIR/bin/hermes-cli" "$PREFIX/bin/hermes"
chmod 755 "$PREFIX/bin/hermes"

echo "==> 5. Instalando serviços runit em $SVDIR/"
mkdir -p "$SVDIR"
for svc in opencodex hermes-gateway hermes-dashboard dashboard-tunnel hermes-watchdog; do
  mkdir -p "$SVDIR/$svc/log"
  cp "$SRC_DIR/services/$svc/run" "$SVDIR/$svc/run"
  cp "$SRC_DIR/services/$svc/log/run" "$SVDIR/$svc/log/run"
  chmod 755 "$SVDIR/$svc/run" "$SVDIR/$svc/log/run"
  rm -f "$SVDIR/$svc/down" 2>/dev/null || true
  echo "    Configurado serviço: $svc"
done

echo "==> 6. Instalando script de boot Termux:Boot"
cp "$SRC_DIR/boot/00-supervisor" "$BOOT_DIR/00-supervisor"
chmod 700 "$BOOT_DIR/00-supervisor"
# Desativar scripts antigos de boot
rm -f "$BOOT_DIR/20-hermes" "$BOOT_DIR/start-server" 2>/dev/null || true

echo "==> 7. Configurando gancho de inicialização no ~/.bashrc"
BASHRC="$HOME/.bashrc"
TOUCH_MARKER="# Hermes High-Availability Daemon Hook"
if [ ! -f "$BASHRC" ] || ! grep -q "$TOUCH_MARKER" "$BASHRC"; then
  cat >> "$BASHRC" << 'EOF'

# Hermes High-Availability Daemon Hook
if ! pgrep -f "runsvdir.*service" >/dev/null 2>&1; then
  (service-daemon start >/dev/null 2>&1 &)
fi
EOF
  echo "    Gancho adicionado ao ~/.bashrc"
fi

echo "==> 8. Rotacionando log histórico grande (hermes-gateway.log)"
if [ -f "$HOME/hermes-gateway.log" ]; then
  LOG_SIZE=$(wc -c < "$HOME/hermes-gateway.log" 2>/dev/null || echo "0")
  if [ "$LOG_SIZE" -gt 10485760 ]; then # > 10MB
    TS=$(date +%Y%m%d_%H%M%S)
    gzip -c "$HOME/hermes-gateway.log" > "$OPS_DIR/logs/hermes-gateway-$TS.log.gz" 2>/dev/null || true
    tail -n 500 "$HOME/hermes-gateway.log" > "$HOME/hermes-gateway.log.tmp" && mv "$HOME/hermes-gateway.log.tmp" "$HOME/hermes-gateway.log"
    echo "    Log grande compactado para $OPS_DIR/logs/hermes-gateway-$TS.log.gz"
  fi
fi

echo "==> 9. Parando loop legado e iniciando supervisor"
pkill -f "20-hermes" 2>/dev/null || true
service-daemon restart >/dev/null 2>&1 || service-daemon start >/dev/null 2>&1 || true

sleep 3
echo "==> Instalação concluída com sucesso!"
echo ""
hermes ps
echo ""
echo "Aguarde 10 segundos para inicialização dos serviços e execute: hermes health"
