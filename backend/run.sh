#!/usr/bin/env bash
# Start the FastAPI backend (creates a venv on first run).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
