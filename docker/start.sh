#!/usr/bin/env sh
set -eu

cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid="$!"

cd /app/frontend
HOSTNAME=0.0.0.0 PORT="${PORT:-7860}" npm run start -- --port "${PORT:-7860}" &
web_pid="$!"

trap 'kill "$api_pid" "$web_pid"' INT TERM
wait "$web_pid"

