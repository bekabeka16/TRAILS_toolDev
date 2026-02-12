#!/usr/bin/env bash
set -e

# Always run from the directory where this script lives (backend/)
cd "$(dirname "$0")"

# Activate venv
source ".venv/bin/activate"

# Run uvicorn via python so PATH issues can’t break it
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
