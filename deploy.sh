#!/usr/bin/env bash
set -euo pipefail

# Minimal, branch-safe deploy script for FastAPI with nohup
# Usage: ./deploy.sh [branch]

BRANCH="${1:-yogesh}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$APP_DIR/logs"
DEPLOY_LOG="$LOG_DIR/deploy.log"
UVICORN_LOG="$LOG_DIR/uvicorn.out"

mkdir -p "$LOG_DIR"
exec >> "$DEPLOY_LOG" 2>&1

echo "--- Deploy started: $(date -u) | branch=$BRANCH | app_dir=$APP_DIR ---"

# Move to app dir
cd "$APP_DIR"

# 1) Stop existing uvicorn processes gracefully
PIDS="$(pgrep -f 'uvicorn' || true)"
if [ -n "$PIDS" ]; then
  echo "Found uvicorn pids: $PIDS — killing..."
  pkill -f 'uvicorn' || true
  sleep 1
fi

# 2) Ensure we have the branch and fetch latest
echo "Fetching from origin..."
git fetch --all --prune

# If branch exists locally, switch; otherwise create tracking branch from origin
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "Switching to local branch $BRANCH"
  git checkout "$BRANCH"
else
  echo "Creating and tracking branch $BRANCH from origin/$BRANCH"
  git checkout -b "$BRANCH" "origin/$BRANCH" || git checkout --track "origin/$BRANCH"
fi

# Reset and pull latest
echo "Resetting to origin/$BRANCH"
git reset --hard "origin/$BRANCH" || true
git clean -fd || true
git pull origin "$BRANCH" || true

# 3) Activate venv if present
if [ -f "$APP_DIR/venv/bin/activate" ]; then
  echo "Activating virtualenv..."
  # shellcheck disable=SC1090
  source "$APP_DIR/venv/bin/activate"
fi

# 4) Install/upgrade requirements (best-effort)
if [ -f requirements.txt ]; then
  echo "Installing requirements..."
  pip install --upgrade -r requirements.txt || echo "pip install failed, continuing"
fi

# 5) (Optional) run migrations - uncomment if you use migrations
# echo "Running migrations..."
# alembic upgrade head || true

# 6) Start uvicorn with nohup
echo "Starting uvicorn (nohup) -> logs: $UVICORN_LOG"
# ensure old nohup output preserved
if [ -f "$UVICORN_LOG" ]; then
  mv "$UVICORN_LOG" "$UVICORN_LOG.$(date +%s)" || true
fi

# start in background
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$UVICORN_LOG" 2>&1 &
NEW_PID=$!
sleep 2


echo "--- Deploy finished: $(date -u) | pid=$NEW_PID ---"

# Print quick tail guidance (not required)
echo "Tail uvicorn logs: tail -n 200 $UVICORN_LOG"
echo "View deploy log: tail -n 200 $DEPLOY_LOG"
