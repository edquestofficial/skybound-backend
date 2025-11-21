#!/usr/bin/env bash
set -euo pipefail

# Optional: pass branch as first arg: ./deploy.sh main
BRANCH="${1:-yogesh}"

# Ensure we are in the app directory where this script is placed
# (When invoked from ssh we cd to the REMOTE_DIR before running this script)
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "Deploy started at $(date). Branch: ${BRANCH}. App dir: ${APP_DIR}"

# 1) Find & kill uvicorn processes (if any)
PIDS="$(pgrep -f 'uvicorn' || true)"
if [ -n "$PIDS" ]; then
  echo "Found uvicorn pids: $PIDS — killing..."
  # pkill may return non-zero when processes already dying; ignore errors
  pkill -f 'uvicorn' || true
  sleep 1
fi

# 2) Reset local changes and pull latest from origin
echo "Cleaning local repo and pulling latest from origin/${BRANCH}..."
git fetch --all --prune
git reset --hard "origin/${BRANCH}"
git clean -fd || true
git pull origin "${BRANCH}" || true

# 3) (Optional) Activate virtualenv if exists
if [ -f "${APP_DIR}/venv/bin/activate" ]; then
  echo "Activating virtualenv..."
  # shellcheck disable=SC1090
  source "${APP_DIR}/venv/bin/activate"
fi

# 4) Install/upgrade requirements (safe to continue on failure)
if [ -f requirements.txt ]; then
  echo "Installing requirements..."
  pip install --upgrade -r requirements.txt || true
fi

# 5) Run DB migrations or other app-specific steps (UNCOMMENT/EDIT)
# echo "Running migrations..."
# alembic upgrade head || true

# 6) Start uvicorn with nohup (adjust the module path: main:app)
echo "Starting uvicorn with nohup..."
# Ensure logs directory exists
mkdir -p logs
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > logs/uvicorn.out 2>&1 &

echo "Deploy finished at $(date). Check logs/uvicorn.out for output."
