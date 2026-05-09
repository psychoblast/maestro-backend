"""
Seed script — inserts 50 placeholder curators into the pitch DB.

Usage:
    python3 seed_curators.py

Run once before going live. Script is idempotent (skips existing IDs).
Tommy must replace contact_email values with real curator emails before deploying.
"""

import json
import sqlite3
import sys
from pathlib import Path

# Match the same DB path logic as pitch_service.py
import os
DB_PATH = Path(os.environ.get("DB_PATH", "/data/memory.db"))
SEED_FILE = Path(__file__).parent / "data" / "curators_seed.json"


def main():
    if not SEED_FILE.exists():
        print(f"ERROR: seed file not found at {SEED_FILE}")
        sys.exit(1)

    records = json.loads(SEED_FILE.read_text())
    print(f"Seed file loaded — {len(records)} curators")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # Ensure table exists (idempotent)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS curators (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            outlet          TEXT DEFAULT '',
            genres          TEXT DEFAULT '[]',
            tier            TEXT DEFAULT 'C',
            contact_email   TEXT NOT NULL,
            notes           TEXT DEFAULT '',
            last_pitched_at TEXT,
            response_rate   REAL DEFAULT 0.0,
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)

    inserted = skipped = 0
    for c in records:
        cur = conn.cursor()
        cur.execute("SELECT id FROM curators WHERE id=?", (c["id"],))
        if cur.fetchone():
            skipped += 1
            continue
        conn.execute(
            """INSERT INTO curators
               (id, name, outlet, genres, tier, contact_email, notes, response_rate)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                c["id"], c["name"], c.get("outlet", ""),
                json.dumps(c.get("genres", [])), c.get("tier", "C"),
                c["contact_email"], c.get("notes", ""),
                c.get("response_rate", 0.0),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Done — inserted: {inserted}, skipped (already exist): {skipped}")
    print(f"Total in DB: {inserted + skipped}")
    print()
    print("REMINDER: Replace all contact_email placeholder@example.com values")
    print("          with real curator emails before going live.")


if __name__ == "__main__":
    main()
