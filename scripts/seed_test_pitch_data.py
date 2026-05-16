"""
Seed script — inserts test artists, curators, and pitches in various states for local dev.

Usage:
    DB_PATH=./test.db python3 scripts/seed_test_pitch_data.py

All IDs are prefixed "test-" so they are easy to identify and purge.
Idempotent — existing IDs are skipped.

Production guard: refuses to run if RAILWAY_ENVIRONMENT=production.
"""

import hashlib
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ENV = os.environ.get("RAILWAY_ENVIRONMENT", "").lower()
if _ENV == "production":
    print("ERROR: seed scripts must not run in production (RAILWAY_ENVIRONMENT=production).")
    sys.exit(1)

DB_PATH = Path(os.environ.get("DB_PATH", "/data/memory.db"))

# ── Seed data ─────────────────────────────────────────────────────────────────

_ARTISTS = [
    {
        "artist_id":   "test-artist-001",
        "artist_name": "Neon Drift",
        "genre":       "indie pop",
        "bio":         "Indie pop duo from Toronto — dreamy synths, honest lyrics.",
    },
    {
        "artist_id":   "test-artist-002",
        "artist_name": "Velvet Static",
        "genre":       "r&b",
        "bio":         "R&B singer-songwriter, London-based, neo-soul influences.",
    },
    {
        "artist_id":   "test-artist-003",
        "artist_name": "Dusk Valley",
        "genre":       "hip hop",
        "bio":         "Hip hop producer and MC from Lagos, West Africa.",
    },
]

_CURATORS = [
    {
        "id": "test-cur-001", "name": "Jordan Ellis", "outlet": "Indie Discovery Weekly",
        "genres": ["indie", "indie pop", "alternative"],
        "tier": "B", "contact_email": "curator-test-001@example.com",
        "notes": "TEST DATA — not a real curator.", "response_rate": 0.35,
    },
    {
        "id": "test-cur-002", "name": "Maya Chen", "outlet": "R&B Radar Newsletter",
        "genres": ["r&b", "soul", "neo-soul"],
        "tier": "A", "contact_email": "curator-test-002@example.com",
        "notes": "TEST DATA — not a real curator.", "response_rate": 0.60,
    },
    {
        "id": "test-cur-003", "name": "Dre Okafor", "outlet": "Hip Hop Unsigned Blog",
        "genres": ["hip hop", "rap", "trap"],
        "tier": "C", "contact_email": "curator-test-003@example.com",
        "notes": "TEST DATA — not a real curator.", "response_rate": 0.10,
    },
]

def _pitch_rows():
    now = datetime.now(timezone.utc)
    return [
        # draft — generated but not sent
        {
            "id": "test-pitch-001", "artist_id": "test-artist-001",
            "curator_id": "test-cur-001", "status": "draft",
            "subject": "[TEST] Neon Drift — Midnight Signal for Indie Discovery",
            "body": "Hi Jordan, we'd love for you to check out our new single.",
            "sent_at": None, "replied_at": None,
        },
        # sent 5 days ago — eligible for Tier B follow-up (day 5 threshold)
        {
            "id": "test-pitch-002", "artist_id": "test-artist-001",
            "curator_id": "test-cur-002", "status": "sent",
            "subject": "[TEST] Neon Drift — Midnight Signal for R&B Radar",
            "body": "Hi Maya, our new track has a neo-soul edge you might enjoy.",
            "sent_at": (now - timedelta(days=5)).isoformat(),
            "replied_at": None,
            "gmail_thread_id": "test-thread-002",
        },
        # replied — positive
        {
            "id": "test-pitch-003", "artist_id": "test-artist-002",
            "curator_id": "test-cur-002", "status": "replied",
            "subject": "[TEST] Velvet Static — Fade for R&B Radar",
            "body": "Hi Maya, Velvet Static's new single has a smooth neo-soul vibe.",
            "sent_at": (now - timedelta(days=10)).isoformat(),
            "replied_at": (now - timedelta(days=7)).isoformat(),
            "gmail_thread_id": "test-thread-003",
        },
        # sent 3 days ago — hip hop artist to tier C curator
        {
            "id": "test-pitch-004", "artist_id": "test-artist-003",
            "curator_id": "test-cur-003", "status": "sent",
            "subject": "[TEST] Dusk Valley — Sahara for Hip Hop Unsigned",
            "body": "Hi Dre, Dusk Valley's new track blends Afrobeats and hip hop.",
            "sent_at": (now - timedelta(days=3)).isoformat(),
            "replied_at": None,
            "gmail_thread_id": "test-thread-004",
        },
    ]


_INTERACTIONS = [
    {
        "id": str(uuid.uuid4()), "pitch_id": "test-pitch-003",
        "direction": "outbound",
        "content": "Subject: [TEST] Velvet Static — Fade for R&B Radar\n\nHi Maya...",
        "sentiment": "neutral",
    },
    {
        "id": str(uuid.uuid4()), "pitch_id": "test-pitch-003",
        "direction": "inbound",
        "content": "From: maya@example.com\n\nLove this! Adding to the playlist next week.",
        "sentiment": "positive",
    },
]


# ── DB helpers ────────────────────────────────────────────────────────────────

def _ensure_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL DEFAULT '{}'
        );
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
        );
        CREATE TABLE IF NOT EXISTS pitches (
            id              TEXT PRIMARY KEY,
            artist_id       TEXT NOT NULL,
            curator_id      TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'draft',
            subject         TEXT NOT NULL,
            body            TEXT NOT NULL,
            sent_at         TEXT,
            replied_at      TEXT,
            gmail_msg_id    TEXT,
            gmail_thread_id TEXT,
            idempotency_key TEXT UNIQUE,
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        );
        CREATE TABLE IF NOT EXISTS pitch_interactions (
            id        TEXT PRIMARY KEY,
            pitch_id  TEXT NOT NULL,
            direction TEXT NOT NULL,
            content   TEXT DEFAULT '',
            sentiment TEXT DEFAULT 'neutral',
            ts        TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        );
    """)
    conn.commit()


def _insert_or_skip(conn, table, id_col, id_val, insert_fn):
    cur = conn.cursor()
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {id_col}=?", (id_val,))
    if cur.fetchone():
        return False
    insert_fn(conn)
    return True


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    _ensure_tables(conn)

    inserted = {"artists": 0, "curators": 0, "pitches": 0, "interactions": 0}

    for a in _ARTISTS:
        def _ins_artist(c, _a=a):
            c.execute("INSERT INTO artists (artist_id, data) VALUES (?,?)",
                      (_a["artist_id"], json.dumps(_a)))
        if _insert_or_skip(conn, "artists", "artist_id", a["artist_id"], _ins_artist):
            inserted["artists"] += 1

    for c in _CURATORS:
        def _ins_curator(conn, _c=c):
            conn.execute(
                "INSERT INTO curators (id,name,outlet,genres,tier,contact_email,notes,response_rate) VALUES (?,?,?,?,?,?,?,?)",
                (_c["id"], _c["name"], _c["outlet"], json.dumps(_c["genres"]),
                 _c["tier"], _c["contact_email"], _c["notes"], _c["response_rate"]),
            )
        if _insert_or_skip(conn, "curators", "id", c["id"], _ins_curator):
            inserted["curators"] += 1

    for p in _pitch_rows():
        idem_key = hashlib.sha256(
            f"{p['artist_id']}:{p['curator_id']}:{p['id']}".encode()
        ).hexdigest()
        def _ins_pitch(conn, _p=p, _k=idem_key):
            conn.execute(
                """INSERT INTO pitches
                   (id,artist_id,curator_id,status,subject,body,sent_at,replied_at,gmail_thread_id,idempotency_key)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (_p["id"], _p["artist_id"], _p["curator_id"], _p["status"],
                 _p["subject"], _p["body"], _p.get("sent_at"), _p.get("replied_at"),
                 _p.get("gmail_thread_id"), _k),
            )
        if _insert_or_skip(conn, "pitches", "id", p["id"], _ins_pitch):
            inserted["pitches"] += 1

    for i in _INTERACTIONS:
        def _ins_int(conn, _i=i):
            conn.execute(
                "INSERT INTO pitch_interactions (id,pitch_id,direction,content,sentiment) VALUES (?,?,?,?,?)",
                (_i["id"], _i["pitch_id"], _i["direction"], _i["content"], _i["sentiment"]),
            )
        if _insert_or_skip(conn, "pitch_interactions", "id", i["id"], _ins_int):
            inserted["interactions"] += 1

    conn.commit()
    conn.close()

    print("Test seed complete:")
    for k, v in inserted.items():
        print(f"  {k}: {v} inserted")
    print()
    print("Test artist IDs: test-artist-001, test-artist-002, test-artist-003")
    print("Test curator IDs: test-cur-001, test-cur-002, test-cur-003")
    print("Test pitch IDs: test-pitch-001..004 (draft/sent/replied states)")
    print()
    print("All test records have IDs prefixed 'test-' for easy identification.")
    print("Remove with: DELETE FROM pitches WHERE id LIKE 'test-%'; (and curators/artists)")


if __name__ == "__main__":
    main()
