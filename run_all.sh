#!/usr/bin/env bash
set -euo pipefail

# carrega .env se existir
if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

HOST="${HOST:-127.0.0.1}"
TEXT_PORT="${TEXT_PORT:-8081}"
VISION_PORT="${VISION_PORT:-8083}"
RELOAD="${RELOAD:-true}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# use o python do venv, se existir
PYTHON="./.venv/Scripts/python.exe"
if [[ ! -f "$PYTHON" ]]; then
  PYTHON="python"   # fallback: requer python no PATH
fi

reload_flag=()
case "${RELOAD,,}" in
  1|true|yes|y|on) reload_flag=(--reload) ;;
esac

"$PYTHON" -m uvicorn services.sextinha_text_api.app.main:app \
  --host "$HOST" --port "$TEXT_PORT" --log-level "$LOG_LEVEL" "${reload_flag[@]}" &
P1=$!
sleep 0.2
"$PYTHON" -m uvicorn services.sextinha_vision_api.app.main:app \
  --host "$HOST" --port "$VISION_PORT" --log-level "$LOG_LEVEL" "${reload_flag[@]}" &
P2=$!

echo "Text PID: $P1 | Vision PID: $P2"
trap 'kill $P1 $P2 2>/dev/null || true' INT TERM EXIT
wait
