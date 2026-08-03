#!/usr/bin/env bash
# 辅酶 Q10 商品培训 · 业务图层编辑器（画面属性面板，与风热证同插件）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/out/editor-logs"
mkdir -p "$LOG_DIR"
PORT="${REVIDEO_EDITOR_PORT:-9001}"
PID_FILE="$LOG_DIR/q10-editor.pid"
LOG_FILE="$LOG_DIR/q10-editor.log"

health_url() {
  curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1 \
    || curl -sf "http://localhost:${PORT}/" >/dev/null 2>&1
}

if [[ -f "$PID_FILE" ]]; then
  old="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    if health_url; then
      echo "Q10 business editor already running pid=$old → http://127.0.0.1:${PORT}/"
      exit 0
    fi
    kill "$old" 2>/dev/null || true
    sleep 1
  fi
fi

if lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  if health_url; then
    echo "Q10 business editor already listening on :${PORT} → http://127.0.0.1:${PORT}/"
    exit 0
  fi
  lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true
  sleep 1
fi

cd "$ROOT"
: >"$LOG_FILE"
nohup node scripts/start-q10-editor.mjs >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"

for i in $(seq 1 45); do
  if health_url; then
    echo "Q10 business editor ready: http://127.0.0.1:${PORT}/"
    echo "pid=$(cat "$PID_FILE")  log=$LOG_FILE"
    echo "panel: 右侧「画面属性」· 点选 editable:q10:* 图层"
    exit 0
  fi
  sleep 1
done

echo "Q10 editor failed to become ready. See $LOG_FILE" >&2
tail -60 "$LOG_FILE" >&2 || true
exit 1
