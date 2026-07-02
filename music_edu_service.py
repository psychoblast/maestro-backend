"""
PLMKR Music-Edu — music-business education action service (mock-first).

Backs the Prof (Education) agent's tool_use loop in /api/chat_stream (see
MUSIC_EDU_TOOLS in main.py). Prof does not just explain the music business — these
functions let the agent take real education actions on the artist's behalf: search
the catalog of music-business courses an artist can study (each carrying the topic
it covers, its difficulty level, its runtime, and how many lessons it holds), build
a concrete, sequenced learning plan by applying a set of matching courses to the
artist's available weekly study time so they get a realistic week-by-week path, and
enroll the artist in a course through their connected learning account so a course
actually gets started on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live LMS/course/enrollment APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_learning_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring airwave_service._airwave_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import math
import os


class LearningAccountNotConnected(Exception):
    """Raised when the artist has not connected a learning (LMS) account.

    Mirrors airwave_service.AirwaveAccountNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your learning account first'
    result instead of crashing the stream.
    """


class LearningAuthExpired(Exception):
    """Raised when a previously connected learning-account authorization expired."""


# ── Course catalog (in-memory reference data) ──────────────────────────────────
# A curated set of music-business education modules an artist can study. Each course
# carries the topic it covers, its difficulty level, its total runtime in minutes,
# and how many discrete lessons it breaks into. The agent can surface the right
# courses for a goal and apply their numbers to build a real, time-boxed learning
# plan. No I/O.
_COURSES = [
    {
        "id": "crs-royalties-101",
        "title": "Royalties 101",
        "topic": "royalties",
        "level": "beginner",
        "duration_min": 120,
        "lessons": 6,
    },
    {
        "id": "crs-publishing-deep",
        "title": "Publishing Deep Dive",
        "topic": "publishing",
        "level": "intermediate",
        "duration_min": 180,
        "lessons": 8,
    },
    {
        "id": "crs-touring-econ",
        "title": "Touring Economics",
        "topic": "touring",
        "level": "intermediate",
        "duration_min": 150,
        "lessons": 7,
    },
    {
        "id": "crs-marketing-fund",
        "title": "Marketing Fundamentals",
        "topic": "marketing",
        "level": "beginner",
        "duration_min": 90,
        "lessons": 5,
    },
    {
        "id": "crs-deal-structures",
        "title": "Record Deal Structures",
        "topic": "deals",
        "level": "advanced",
        "duration_min": 210,
        "lessons": 9,
    },
    {
        "id": "crs-sync-licensing",
        "title": "Sync Licensing Basics",
        "topic": "sync",
        "level": "beginner",
        "duration_min": 100,
        "lessons": 5,
    },
]


async def search_courses(topic: str = "", level: str = "") -> dict:
    """Search the course catalog by the topic a course covers and/or its level.

    Both filters are optional and matched case-insensitively as substrings.
    ``topic`` matches the course's topic (e.g. "royalties", "publishing",
    "touring", "marketing", "deals", "sync"), and ``level`` matches its difficulty
    (e.g. "beginner", "intermediate", "advanced"). Returns
    {"courses": [...], "count": int}. Pure — no I/O.
    """
    tp = (topic or "").strip().lower()
    lv = (level or "").strip().lower()
    matches = [
        dict(c)
        for c in _COURSES
        if (not tp or tp in c["topic"].lower())
        and (not lv or lv in c["level"].lower())
    ]
    return {"courses": matches, "count": len(matches)}


def _get_course(course_id: str) -> dict | None:
    cid = (course_id or "").strip()
    for c in _COURSES:
        if c["id"] == cid:
            return c
    return None


async def build_learning_plan(
    artist_id: str,
    topic: str = "",
    level: str = "",
    weekly_hours: int = 0,
) -> dict:
    """Build a sequenced learning plan by applying matching courses to study time.

    Deterministic plan construction — never contacts an LMS or enrollment API.
    Selects the courses matching ``topic`` (and optional ``level``), sums their
    runtime and lessons, and — given the artist's available ``weekly_hours`` —
    estimates how many weeks the plan takes to finish. Returns a structured plan
    with the ordered course list, totals, gaps, and a recommendation of
    "start" / "revise" / "blocked".
    """
    tp = (topic or "").strip()
    lv = (level or "").strip()
    try:
        hours = int(weekly_hours or 0)
    except (TypeError, ValueError):
        hours = 0

    found = await search_courses(topic=tp, level=lv)
    courses = found["courses"]

    gaps = []
    if not tp:
        gaps.append("missing_topic")
    elif not courses:
        gaps.append("no_matching_courses")
    if hours <= 0:
        gaps.append("missing_weekly_hours")

    total_minutes = sum(c["duration_min"] for c in courses)
    total_lessons = sum(c["lessons"] for c in courses)
    weeks_to_complete = 0
    if courses and hours > 0:
        weeks_to_complete = int(math.ceil(total_minutes / (hours * 60.0)))

    plan = [
        {"course_id": c["id"], "title": c["title"], "lessons": c["lessons"],
         "duration_min": c["duration_min"]}
        for c in courses
    ]

    if not tp or not courses:
        # Without a topic that resolves to real courses the plan cannot be built.
        recommendation = "blocked"
    elif gaps or weeks_to_complete <= 0:
        recommendation = "revise"
    else:
        recommendation = "start"
    viable = recommendation == "start"

    return {
        "viable": viable,
        "gaps": gaps,
        "topic": tp,
        "level": lv,
        "weekly_hours": hours,
        "plan": plan,
        "course_count": len(courses),
        "total_minutes": total_minutes,
        "total_lessons": total_lessons,
        "weeks_to_complete": weeks_to_complete,
        "recommendation": recommendation,
    }


def _learning_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's learning (LMS) account.

    In production this would look up a stored learning-account link for the artist.
    Here it is driven purely by the ``MUSIC_EDU_ACCOUNT_CONNECTED`` env flag so tests
    can toggle connected / expired / not-connected with ZERO network calls and NO
    real secret. Values:
      - "expired"                     → raise LearningAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("MUSIC_EDU_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise LearningAuthExpired("learning-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def enroll_in_course(
    artist_id: str,
    course_id: str,
    start_date: str = "",
) -> dict:
    """Enroll the artist in a course via their connected learning account.

    Raises LearningAccountNotConnected / LearningAuthExpired when no learning account
    is linked so the caller can surface a 'connect your learning account' message
    instead of a hard failure. When the course id is unknown, returns a structured
    {"status": "unknown_course"} result rather than raising. On success returns a
    deterministic mock enrollment reference — NO network call is ever made and no
    enrollment is actually created.
    """
    if not _learning_account_connected(artist_id):
        raise LearningAccountNotConnected(
            "artist has not connected a learning (LMS) account"
        )
    course = _get_course(course_id)
    if course is None:
        return {"status": "unknown_course", "course_id": (course_id or "").strip()}
    sd = (start_date or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{course['id']}:{sd}".encode("utf-8")
    ).hexdigest()
    reference = "ENROLL-" + digest[:10].upper()
    return {
        "status": "enrolled",
        "reference": reference,
        "course_id": course["id"],
        "course_title": course["title"],
        "start_date": sd,
    }
