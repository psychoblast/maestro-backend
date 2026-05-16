"""
Seed script — inserts PR contacts into the pr_contacts table.

Usage:
    DB_PATH=/data/memory.db python3 scripts/seed_pr_contacts.py

Run once before going live. Idempotent — existing IDs are skipped.
Replace every contact_email placeholder before sending real pitches.

Production guard: refuses to run if RAILWAY_ENVIRONMENT=production.
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

_ENV = os.environ.get("RAILWAY_ENVIRONMENT", "").lower()
if _ENV == "production":
    print("ERROR: seed scripts must not run in production (RAILWAY_ENVIRONMENT=production).")
    print("Use the Railway shell only for emergency data repair, not seeding.")
    sys.exit(1)

DB_PATH   = Path(os.environ.get("DB_PATH", "/data/memory.db"))
SEED_FILE = Path(__file__).parent.parent / "data" / "pr_contacts_seed.json"


def main():
    if not SEED_FILE.exists():
        print(f"ERROR: seed file not found at {SEED_FILE}")
        sys.exit(1)

    records = json.loads(SEED_FILE.read_text())
    print(f"Seed file loaded — {len(records)} PR contacts")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pr_contacts (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            outlet_type     TEXT DEFAULT '',
            outlet_name     TEXT DEFAULT '',
            genres          TEXT DEFAULT '[]',
            tier            TEXT DEFAULT 'C',
            contact_email   TEXT NOT NULL,
            beat            TEXT DEFAULT '',
            notes           TEXT DEFAULT '',
            last_pitched_at TEXT,
            response_rate   REAL DEFAULT 0.0,
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)

    inserted = skipped = 0
    for c in records:
        cur = conn.cursor()
        cur.execute("SELECT id FROM pr_contacts WHERE id=?", (c["id"],))
        if cur.fetchone():
            skipped += 1
            continue
        conn.execute(
            """INSERT INTO pr_contacts
               (id, name, outlet_type, outlet_name, genres, tier, contact_email, beat, notes, response_rate)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                c["id"], c["name"],
                c.get("outlet_type", ""), c.get("outlet_name", ""),
                json.dumps(c.get("genres", [])), c.get("tier", "C"),
                c["contact_email"], c.get("beat", ""),
                c.get("notes", ""), c.get("response_rate", 0.0),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Done — inserted: {inserted}, skipped (already exist): {skipped}")
    print(f"Total in DB: {inserted + skipped}")
    print()
    print("REMINDER: Replace all contact_email placeholder@example.com values")
    print("          with real journalist/editor emails before going live.")


if __name__ == "__main__":
    main()
