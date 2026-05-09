#!/usr/bin/env python3
"""
Export FastAPI's OpenAPI schema to docs/openapi.json.

Usage:
    python3 scripts/export_openapi.py

Sets minimal env vars so imports don't fail on missing credentials.
Output: docs/openapi.json
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Set minimal env vars to prevent import errors on missing credentials
_tmp = ROOT / ".openapi_tmp"
_tmp.mkdir(exist_ok=True)
os.environ.setdefault("DB_PATH",        str(_tmp / "memory.db"))
os.environ.setdefault("AUDIO_CACHE_DIR",str(_tmp / "audio_cache"))
os.environ.setdefault("DATABASE_URL",   "")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-placeholder")
os.environ.setdefault("SCHEDULER_ENABLED", "false")

# Import the FastAPI app — this runs module-level init (DB create, scheduler)
print("Importing app...")
from main import app  # noqa: E402

schema = app.openapi()
out    = ROOT / "docs" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(schema, indent=2))
print(f"OpenAPI schema written to {out}")
print(f"Endpoints documented: {len(schema.get('paths', {}))}")
