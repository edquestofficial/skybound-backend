#!/usr/bin/env bash
set -e

BRANCH=${1:-main}

echo "🔄 Deploying branch: $BRANCH"
echo "📁 Current directory: $(pwd)"

# Pull latest code
echo "➡ Fetching latest code..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

# Activate virtual environment
echo "➡ Activating virtualenv..."
source .venv/bin/activate

# Install/Update dependencies
echo "➡ Installing dependencies with uv..."
uv sync

# Restart FastAPI service
echo "➡ Restarting fastapi.service..."
sudo systemctl restart fastapi

echo "✅ Deployment completed!"
