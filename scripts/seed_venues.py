"""
Seed script — inserts booking contacts (venues, festivals, promoters) into the booking_contacts table.

Usage:
    DB_PATH=/data/memory.db python3 scripts/seed_venues.py

Run once before going live. Idempotent — existing IDs are skipped.
Replace every contact_email placeholder before sending real inquiries.

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
SEED_FILE = Path(__file__).parent.parent / "data" / "booking_contacts_seed.json"


def main():
    if not SEED_FILE.exists():
        print(f"ERROR: seed file not found at {SEED_FILE}")
        sys.exit(1)

    records = json.loads(SEED_FILE.read_text())
    print(f"Seed file loaded — {len(records)} booking contacts")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS booking_contacts (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            venue_or_festival TEXT DEFAULT '',
            type            TEXT DEFAULT 'venue',
            city            TEXT DEFAULT '',
            country         TEXT DEFAULT '',
            capacity        INTEGER DEFAULT 0,
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
        cur.execute("SELECT id FROM booking_contacts WHERE id=?", (c["id"],))
        if cur.fetchone():
            skipped += 1
            continue
        conn.execute(
            """INSERT INTO booking_contacts
               (id, name, venue_or_festival, type, city, country, capacity,
                genres, tier, contact_email, notes, response_rate)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                c["id"], c["name"],
                c.get("venue_or_festival", ""), c.get("type", "venue"),
                c.get("city", ""), c.get("country", ""),
                c.get("capacity", 0),
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
    print("          with real booker/promoter emails before going live.")


if __name__ == "__main__":
    main()
