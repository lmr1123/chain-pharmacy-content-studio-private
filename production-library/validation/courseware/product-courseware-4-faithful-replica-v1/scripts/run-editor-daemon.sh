#!/usr/bin/env bash
# Durable video editor process (project Revideo flow).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/out/editor-logs"
mkdir -p "$LOG_DIR"
PORT="${REVIDEO_EDITOR_PORT:-9012}"
PID_FILE="$LOG_DIR/editor.pid"
LOG_FILE="$LOG_DIR/editor.log"

if [[ -f "$PID_FILE" ]]; then
  old="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
      echo "Editor already running pid=$old → http://127.0.0.1:${PORT}/"
      exit 0
    fi
    kill "$old" 2>/dev/null || true
    sleep 1
  fi
fi

if lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true
  sleep 1
fi

cd "$ROOT"
# ensure stills exist
if [[ ! -f "$ROOT/out/scene-stills/S00_cover.png" ]]; then
  python3 scripts/export-full-film-video.py >>"$LOG_FILE" 2>&1 || true
fi

nohup node scripts/start-cw4-editor.mjs >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
sleep 3
if curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "Courseware-4 VIDEO editor ready: http://127.0.0.1:${PORT}/"
  echo "pid=$(cat "$PID_FILE")  log=$LOG_FILE"
  exit 0
fi
echo "Editor failed to become ready. See $LOG_FILE" >&2
tail -50 "$LOG_FILE" >&2 || true
exit 1
