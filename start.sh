#!/bin/bash
cd /home/tommy/maestro

echo ""
echo "  Maestro — AI Artist Team"
echo "  Open: http://localhost:8765"
echo ""

# Load env vars from ~/.bashrc (picks up API keys set there)
# shellcheck disable=SC1090
[ -f ~/.bashrc ] && source ~/.bashrc

# Local path overrides (cloud/Docker uses env vars from railway.json / .env)
export SKILLS_DIR="${SKILLS_DIR:-/home/tommy/.openclaw/workspace/skills}"
export ARTISTS_DIR="${ARTISTS_DIR:-/home/tommy/.openclaw/workspace/maestro/data/artists}"
export KNOWLEDGE_BASE="${KNOWLEDGE_BASE:-/home/tommy/.openclaw/workspace/KNOWLEDGE.md}"

python3 -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
