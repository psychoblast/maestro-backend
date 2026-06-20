import os
import re
import io
import sys
import json
import time
import uuid
import secrets
import base64
import random
import tempfile
import asyncio
import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

# Boot: structured logging must be configured before any other module imports
from logging_config import setup_logging, get_logger, bind_request_id
setup_logging()
log = get_logger("main")

from error_reporting import init_error_reporting, capture_exception
init_error_reporting()

from ar_scout_loader import build_ar_scout_system_prompt
from grid_prophet_loader import build_grid_prophet_system_prompt
from sync_agent_loader import build_sync_agent_system_prompt
from brand_connect_loader import build_brand_connect_system_prompt
from lex_cipher_loader import build_lex_cipher_system_prompt
from tour_commander_loader import build_tour_commander_system_prompt
from ink_and_air_loader import build_ink_and_air_system_prompt
from royalty_doctor_loader import build_royalty_doctor_system_prompt

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse as _RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import anthropic
import httpx

ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_AVAILABLE = bool(ANTHROPIC_API_KEY)

# A&R assessment mock mode — default ON so no live Anthropic calls during testing
AR_SCOUT_MOCK_MODE       = os.environ.get("AR_SCOUT_MOCK_MODE",       "true").lower() != "false"
# Marketing assessment mock mode — default ON so no live Anthropic calls during testing
GRID_PROPHET_MOCK_MODE   = os.environ.get("GRID_PROPHET_MOCK_MODE",   "true").lower() != "false"
# Sync licensing assessment mock mode — default ON so no live Anthropic calls during testing
SYNC_AGENT_MOCK_MODE     = os.environ.get("SYNC_AGENT_MOCK_MODE",     "true").lower() != "false"
# Brand Connect assessment mock mode — default ON so no live Anthropic calls during testing
BRAND_CONNECT_MOCK_MODE  = os.environ.get("BRAND_CONNECT_MOCK_MODE",  "true").lower() != "false"
# Legal (Lex-Cipher) assessment mock mode — default ON so no live Anthropic calls during testing
LEX_CIPHER_MOCK_MODE     = os.environ.get("LEX_CIPHER_MOCK_MODE",     "true").lower() != "false"
# Tour & Live (Tour-Commander) assessment mock mode — default ON so no live Anthropic calls during testing
TOUR_COMMANDER_MOCK_MODE = os.environ.get("TOUR_COMMANDER_MOCK_MODE", "true").lower() != "false"
# Publishing & Rights (Ink-and-Air) assessment mock mode — default ON so no live Anthropic calls during testing
INK_AND_AIR_MOCK_MODE    = os.environ.get("INK_AND_AIR_MOCK_MODE",    "true").lower() != "false"
ROYALTY_DOCTOR_MOCK_MODE = os.environ.get("ROYALTY_DOCTOR_MOCK_MODE", "true").lower() != "false"

# Base directory: defaults to the folder containing this file so both local
# and Docker deployments work without explicit env overrides.
_BASE = Path(__file__).parent

SKILLS_DIR    = Path(os.environ.get("SKILLS_DIR",     _BASE / "skills"))
ARTISTS_DIR   = Path(os.environ.get("ARTISTS_DIR",    "/data/artists"))
KNOWLEDGE_BASE= Path(os.environ.get("KNOWLEDGE_BASE", _BASE / "KNOWLEDGE.md"))
AUDIO_CACHE   = Path(os.environ.get("AUDIO_CACHE_DIR", "/data/audio_cache"))
AUDIO_CACHE.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES    = int(os.environ.get("MAX_UPLOAD_SIZE", str(25 * 1024 * 1024)))  # 25 MB default
_ALLOWED_AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".webm"}

# Cloud integrations (optional — graceful degradation when absent)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
ELEVENLABS_API_KEY    = os.environ.get("ELEVENLABS_API_KEY", "")
DATABASE_URL: str     = os.environ.get("DATABASE_URL", "")  # Railway PostgreSQL — persists artist profiles


# API key auth — set PLMKR_API_KEY in Railway env; unset = dev-permissive mode
_PLMKR_API_KEY        = os.environ.get("PLMKR_API_KEY", "")

# CORS — defaults cover Railway backend + Vercel frontend + local dev.
# Override by setting ALLOWED_ORIGINS as a comma-separated list in Railway env vars.
_DEFAULT_CORS_ORIGINS = [
    "https://maestro-backend-production.up.railway.app",
    "https://plmkr.vercel.app",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
_raw_origins   = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins else _DEFAULT_CORS_ORIGINS
)


# Sync client for non-streaming endpoints, async client for streaming
client       = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or "placeholder")
async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY or "placeholder")

if not ANTHROPIC_AVAILABLE:
    log.warning("boot_warning", extra={"event": "boot_warning", "key": "ANTHROPIC_API_KEY",
                "detail": "AI agent chat and handoff routes will return HTTP 503. Set ANTHROPIC_API_KEY to enable."})

# ── Agent roster ───────────────────────────────────────────────────────────────
AGENTS = [
    {"id": "puppet-master",    "name": "Marcus",  "title": "Artist Manager",       "skill": "maestro-puppet-master",    "voice": "am_onyx",      "color": "#7C3AED", "emoji": "🎯", "specialty": "Career strategy, deal analysis, team coordination"},
    {"id": "lex-cipher",       "name": "Lex",     "title": "Entertainment Lawyer", "skill": "maestro-lex-cipher",       "voice": "af_jessica",   "color": "#1D4ED8", "emoji": "⚖️", "specialty": "Contracts, IP, legal protection"},
    {"id": "fund-phantom",     "name": "Jade",    "title": "Grants & Funding",     "skill": "maestro-fund-phantom",     "voice": "af_heart",     "color": "#047857", "emoji": "💰", "specialty": "Grants, funding, arts council applications"},
    {"id": "rights-pulse",     "name": "Ray",     "title": "Performance Rights",   "skill": "maestro-rights-pulse",     "voice": "am_echo",      "color": "#B45309", "emoji": "🎼", "specialty": "PRO registration, performance royalties"},
    {"id": "border-royalty",   "name": "Cleo",    "title": "Neighbouring Rights",  "skill": "maestro-border-royalty",   "voice": "bf_alice",     "color": "#6D28D9", "emoji": "🌍", "specialty": "Neighbouring rights, international royalties"},
    {"id": "mech-ledger",      "name": "Finn",    "title": "Mechanical Royalties", "skill": "maestro-mech-ledger",      "voice": "am_puck",      "color": "#0369A1", "emoji": "⚙️", "specialty": "Mechanical royalties, licensing rates"},
    {"id": "vault-keeper",     "name": "Victor",  "title": "Business Manager",     "skill": "maestro-vault-keeper",     "voice": "bm_george",    "color": "#065F46", "emoji": "🏦", "specialty": "Budgets, cashflow, business finances"},
    {"id": "ledger-lock",      "name": "Nadia",   "title": "Accountant",           "skill": "maestro-ledger-lock",      "voice": "bf_emma",      "color": "#1E40AF", "emoji": "📊", "specialty": "Tax, bookkeeping, royalty statements"},
    {"id": "signal-blaster",   "name": "Zara",    "title": "Publicist",            "skill": "maestro-signal-blaster",   "voice": "af_bella",     "color": "#9D174D", "emoji": "📣", "specialty": "Press, media, PR campaigns"},
    {"id": "grid-prophet",     "name": "Kai",     "title": "Digital Marketing",    "skill": "maestro-grid-prophet",     "voice": "am_adam",      "color": "#7C2D12", "emoji": "📱", "specialty": "Social media, digital growth, algorithms"},
    {"id": "vision-forge",     "name": "Luna",    "title": "AI Visuals",           "skill": "maestro-vision-forge",     "voice": "af_sky",       "color": "#4C1D95", "emoji": "🎨", "specialty": "AI-generated artwork, visual identity"},
    {"id": "design-studio",    "name": "Diego",   "title": "Brand Designer",       "skill": "maestro-design-studio",    "voice": "em_alex",      "color": "#713F12", "emoji": "✏️", "specialty": "Branding, logo, visual assets"},
    {"id": "venue-hawk",       "name": "Ray B",   "title": "Booking Agent",        "skill": "maestro-venue-hawk",       "voice": "am_fenrir",    "color": "#134E4A", "emoji": "🎤", "specialty": "Venue booking, show deals, routing"},
    {"id": "tour-commander",   "name": "Miles",   "title": "Tour Manager",         "skill": "maestro-tour-commander",   "voice": "bm_lewis",     "color": "#1E3A5F", "emoji": "🚌", "specialty": "Tour logistics, production, crew"},
    {"id": "airwave",          "name": "Solo",    "title": "Radio & Playlist",     "skill": "maestro-airwave",          "voice": "am_liam",      "color": "#166534", "emoji": "📻", "specialty": "Radio plugging, playlist pitching"},
    {"id": "brand-connect",    "name": "Nia",     "title": "Brand Partnerships",   "skill": "maestro-brand-connect",    "voice": "af_nova",      "color": "#831843", "emoji": "🤝", "specialty": "Brand deals, endorsements, sponsorships"},
    {"id": "merch-empire",     "name": "Max",     "title": "Merchandise",          "skill": "maestro-merch-empire",     "voice": "am_michael",   "color": "#78350F", "emoji": "👕", "specialty": "Merch design, production, fulfillment"},
    {"id": "fan-builder",      "name": "Aria",    "title": "Fan Engagement",       "skill": "maestro-fan-builder",      "voice": "af_aoede",     "color": "#5B21B6", "emoji": "❤️", "specialty": "Community building, fan clubs, superfans"},
    {"id": "sync-agent",       "name": "Sync",    "title": "Sync Licensing",       "skill": "maestro-sync-agent",       "voice": "bf_isabella",  "color": "#0C4A6E", "emoji": "🎬", "specialty": "TV, film, ad sync placements"},
    {"id": "global-scout",     "name": "Nova",    "title": "International",        "skill": "maestro-global-scout",     "voice": "af_sarah",     "color": "#064E3B", "emoji": "🌐", "specialty": "Global market entry, international deals"},
    {"id": "creative-director","name": "Cree",    "title": "Creative Director",    "skill": "maestro-creative-director","voice": "af_river",     "color": "#3B0764", "emoji": "🎭", "specialty": "Creative vision, rollout strategy, aesthetics"},
    {"id": "data-oracle",      "name": "Data",    "title": "Analytics",            "skill": "maestro-data-oracle",      "voice": "am_eric",      "color": "#1C1917", "emoji": "📈", "specialty": "Streaming data, audience analytics, DSP insights"},
    {"id": "ar-scout",         "name": "Scout",   "title": "A&R",                  "skill": "maestro-ar-scout",         "voice": "af_kore",      "color": "#292524", "emoji": "🔍", "specialty": "Sound development, A&R strategy, demo feedback"},
    {"id": "producer-connect", "name": "Beat",    "title": "Production",           "skill": "maestro-producer-connect", "voice": "am_santa",     "color": "#44403C", "emoji": "🎧", "specialty": "Producer connections, beat licensing, co-writes"},
    {"id": "music-edu",        "name": "Prof",    "title": "Education",            "skill": "maestro-music-edu",        "voice": "bm_daniel",    "color": "#1E3A5F", "emoji": "🎓", "specialty": "Music business education, industry knowledge"},
    {"id": "collab-connect",   "name": "Collab",  "title": "Networking",           "skill": "maestro-collab-connect",   "voice": "af_nicole",    "color": "#14532D", "emoji": "🔗", "specialty": "Artist collaborations, networking, features"},
    {"id": "artist-wellness",  "name": "Maya",    "title": "Wellness",             "skill": "maestro-artist-wellness",  "voice": "hf_alpha",     "color": "#4A1942", "emoji": "🧘", "specialty": "Mental health, work-life balance, burnout prevention"},
    {"id": "press-monitor",    "name": "Press",   "title": "Media Monitor",        "skill": "maestro-press-monitor",    "voice": "af_alloy",     "color": "#27272A", "emoji": "📰", "specialty": "Press tracking, sentiment, media coverage"},
    {"id": "live-coach",       "name": "Coach",   "title": "Performance Coach",    "skill": "maestro-live-coach",       "voice": "hm_omega",     "color": "#1C1917", "emoji": "🎙️", "specialty": "Stage presence, vocals, live performance"},
    {"id": "audio-quality",    "name": "Audio",   "title": "Quality Control",      "skill": "maestro-audio-quality",    "voice": "im_nicola",    "color": "#0F172A", "emoji": "🔊", "specialty": "Mix feedback, mastering standards, audio QC"},
    {"id": "ai-navigator",     "name": "Neo",     "title": "AI Tools",             "skill": "maestro-ai-navigator",     "voice": "hm_psi",       "color": "#1E1B4B", "emoji": "🤖", "specialty": "AI tools, automation, tech stack for artists"},
    {"id": "royalty-doctor",   "name": "Doc",     "title": "Royalty Recovery",     "skill": "maestro-royalty-doctor",   "voice": "bm_fable",     "color": "#0C4A6E", "emoji": "💊", "specialty": "Unclaimed royalties, black box money, audits"},
    {"id": "video-director",   "name": "Reel",    "title": "Music Video",          "skill": "maestro-video-director",   "voice": "em_santa",     "color": "#1A1A2E", "emoji": "🎥", "specialty": "Music video production, directors, budgets"},
    {"id": "mobile-monetize",  "name": "Mo",      "title": "Monetization",         "skill": "maestro-mobile-monetize",  "voice": "am_michael",   "color": "#064E3B", "emoji": "📲", "specialty": "TikTok, YouTube, mobile platform monetization"},
    {"id": "storefront",       "name": "Store",   "title": "Fan Store",            "skill": "maestro-storefront",       "voice": "bf_lily",      "color": "#3B0764", "emoji": "🛍️", "specialty": "Direct-to-fan store, digital products, memberships"},
    {"id": "ink-and-air",      "name": "Reed",    "title": "Music Publisher",      "skill": "maestro-ink-and-air",      "voice": "pm_alex",      "color": "#1E3A5F", "emoji": "📝", "specialty": "Publishing deals, sync licensing, songwriting royalties"},
    {"id": "live-wire",        "name": "Knox",    "title": "Booking Agent",        "skill": "maestro-live-wire",        "voice": "zm_yunxi",     "color": "#7F1D1D", "emoji": "🎤", "specialty": "Live shows, touring, festival bookings, performance fees"},
    {"id": "label-services",   "name": "Tommy",   "title": "Label Services",       "skill": "maestro-label-services",   "voice": "bm_george",    "color": "#0F172A", "emoji": "🏷️", "specialty": "Distribution, release planning, label setup, delivery to DSPs"},
    {"id": "content-forge",    "name": "Pen",     "title": "Content Creation",     "skill": "maestro-content-forge",    "voice": "if_sara",      "color": "#1C1917", "emoji": "✍️", "specialty": "Captions, bios, press releases, content strategy"},
    {"id": "schedule-keeper",  "name": "Cal",     "title": "Scheduling",           "skill": "maestro-schedule-keeper",  "voice": "af_sarah",     "color": "#27272A", "emoji": "📅", "specialty": "Calendar, release scheduling, deadline management"},
    {"id": "pr-agent",         "name": "Quinn",   "title": "PR Manager",           "skill": "maestro-pr-agent",         "voice": "af_nova",      "color": "#BE185D", "emoji": "📰", "specialty": "Press outreach, blogs, podcasts, magazines, editorial placement"},
    {"id": "booking-agent",    "name": "Avery",   "title": "Booking Agent",        "skill": "maestro-booking-agent",    "voice": "bm_fable",     "color": "#0F766E", "emoji": "🎤", "specialty": "Venue booking, festival pitching, promoter outreach, show deals"},
    {"id": "social-manager",   "name": "Riley",   "title": "Social Media Manager", "skill": "maestro-social-manager",   "voice": "af_sky",       "color": "#0EA5E9", "emoji": "📲", "specialty": "Social post strategy, Buffer scheduling, platform-specific content, trend awareness"},
    {"id": "release-strategist","name": "Sage",   "title": "Release Strategist",   "skill": "maestro-release-strategist","voice": "af_jessica",   "color": "#7C3AED", "emoji": "🚀", "specialty": "Release planning, campaign orchestration, cross-phase launch strategy"},
]

AGENTS_BY_ID = {a["id"]: a for a in AGENTS}

# ── Pre-load all SKILL.md files at startup ─────────────────────────────────────
SKILLS_CACHE: dict[str, str] = {}

def _preload_skills() -> None:
    loaded, missing = 0, 0
    for a in AGENTS:
        p = SKILLS_DIR / a["skill"] / "SKILL.md"
        if p.exists():
            SKILLS_CACHE[a["skill"]] = p.read_text()
            loaded += 1
        else:
            missing += 1
    log.info("skills_preloaded", extra={"event": "skills_preloaded", "loaded": loaded, "missing": missing})

_preload_skills()

# ── Static greetings for ALL agents — zero API calls on agent open ─────────────
#
# FORMAT: one warm, specific, first-person sentence.
# Each agent states their name, title, and one concrete thing they handle.
# No questions. No markdown. Natural spoken cadence.
# Marcus has a rotating pool; all others have 3 variants for variety.
#
_AGENT_GREETINGS: dict[str, list[str]] = {
    "puppet-master": [
        "Hey, I'm Marcus — your Artist Manager at Playmaker. I run point on your entire career, from deals to team coordination. What's the most pressing thing on your plate right now?",
        "I'm Marcus, your Artist Manager at Playmaker. From contract strategy to connecting you with the right specialists, everything runs through me. What do you need to move on today?",
        "Marcus here — your Artist Manager at Playmaker. I've got full visibility across your operation: legal, finance, marketing, touring, all of it. What's going on with your career right now?",
        "Good to connect. I'm Marcus, your Artist Manager at Playmaker — every major decision, deal, and direction goes through me first. What's the priority today?",
        "I'm Marcus, your Artist Manager at Playmaker — strategy, deals, and your full team all run through me. I'm here whenever you need to think through a move. What's on your mind?",
    ],
    "lex-cipher": [
        "I'm Lex, your Entertainment Lawyer at Playmaker. I handle contracts, IP protection, and making sure no one takes advantage of you in a deal. What legal situation are we looking at?",
        "Lex here — your Entertainment Lawyer at Playmaker. Whether it's a record deal, publishing agreement, or a rights dispute, I've got you covered. What do you need reviewed?",
        "I'm Lex, your Entertainment Lawyer at Playmaker. I read every clause so you don't have to. What contract or legal question is on the table?",
    ],
    "fund-phantom": [
        "I'm Jade, your Grants and Funding specialist at Playmaker. I find and secure money that artists leave on the table — arts council grants, government funding, and private opportunities. What stage are you at?",
        "Jade here — Grants and Funding at Playmaker. I specialise in grants and arts funding. There's more money available for independent artists than most realise. Let's find what you qualify for.",
        "I'm Jade, your Funding specialist at Playmaker. From FACTOR to arts councils to private foundations, I know where the money is and how to apply for it. What do you need?",
    ],
    "rights-pulse": [
        "I'm Ray, your Performance Rights specialist at Playmaker. I make sure you're registered with the right PROs and collecting every penny you're owed in performance royalties. Where are we at?",
        "Ray here — Performance Rights at Playmaker. If you're not properly registered with your PRO, you're leaving money on the table every time your music plays. Let's sort that out.",
        "I'm Ray, your Performance Rights officer at Playmaker. PRO registration, performance royalties, live performance income — that's my world. What do you need to get set up?",
    ],
    "border-royalty": [
        "I'm Cleo, your Neighbouring Rights specialist at Playmaker. If your recordings are played on radio or in public spaces, you're owed money most artists never collect. Let's fix that.",
        "Cleo here — Neighbouring Rights at Playmaker. I handle neighbouring rights and international royalty collection. There's money sitting unclaimed in markets around the world with your name on it.",
        "I'm Cleo, your Neighbouring Rights advisor at Playmaker. Master recording royalties from broadcast and public performance are separate from your PRO income — and often overlooked. I'll walk you through it.",
    ],
    "mech-ledger": [
        "I'm Finn, your Mechanical Royalties specialist at Playmaker. Every time someone streams or downloads your music, mechanical royalties are generated. I make sure you collect all of them.",
        "Finn here — Mechanical Royalties at Playmaker. Whether it's streaming mechanicals, download licenses, or physical reproduction, I track the rates and make sure you're paid correctly.",
        "I'm Finn, your Mechanical Royalties advisor at Playmaker. Publishing income, licensing rates, Harry Fox, MLC — I handle the mechanical side of your publishing income. What do you need?",
    ],
    "vault-keeper": [
        "I'm Victor, your Business Manager at Playmaker. I oversee your finances at the macro level — budgets, cashflow, business structure, and making sure your money is working for you.",
        "Victor here — Business Management at Playmaker. Think of me as the CFO for your music career. I handle the financial strategy so you can focus on the music.",
        "I'm Victor, your Business Manager at Playmaker. Revenue planning, expense management, entity structure — I keep the business side of your career solid. What are we working on?",
    ],
    "ledger-lock": [
        "I'm Nadia, your Accountant at Playmaker. Tax returns, bookkeeping, royalty statement reconciliation — I make sure your numbers are clean and you keep as much of your income as legally possible.",
        "Nadia here — Accounting and Tax at Playmaker. Tour expenses, recording deductions, quarterly filings — I handle the detail work that protects your income. What do you need sorted?",
        "I'm Nadia, your Accountant at Playmaker. I specialise in music industry taxation — there are deductions most artists miss entirely. Let's make sure you're not one of them.",
    ],
    "signal-blaster": [
        "I'm Zara, your Publicist at Playmaker. Press coverage, media strategy, narrative control — I make sure the right people are talking about you in the right way. What's the story we're telling?",
        "Zara here — PR and Press at Playmaker. From release campaigns to crisis management, I handle your relationship with the media. What are we launching or protecting?",
        "I'm Zara, your Publicist at Playmaker. Blogs, magazines, radio interviews, editorial features — I open those doors and make sure you walk through them looking great. What do you need?",
    ],
    "grid-prophet": [
        "I'm Kai, your Digital Marketing specialist at Playmaker. Social growth, platform algorithms, paid campaigns — I turn your online presence into a career asset. What platform are we focused on?",
        "Kai here — Digital Marketing at Playmaker. TikTok strategy, Instagram growth, YouTube optimisation, Facebook ads — I know what moves the needle online for independent artists.",
        "I'm Kai, your Digital Marketing advisor at Playmaker. Data-driven growth across every platform. I'll show you exactly where to spend your time and money for maximum return.",
    ],
    "vision-forge": [
        "I'm Luna, your AI Visuals specialist at Playmaker. Album artwork, press photos, video thumbnails, brand visuals — I use AI tools to create professional-grade imagery at a fraction of the cost.",
        "Luna here — AI Visuals at Playmaker. Whether it's a full visual identity or a single cover, I use the latest AI image tools to bring your creative vision to life fast.",
        "I'm Luna, your AI Visuals advisor at Playmaker. I'll help you create a consistent, striking visual world for your music using the best AI image and video tools available.",
    ],
    "design-studio": [
        "I'm Diego, your Brand Designer at Playmaker. Logo, typography, colour palette, visual identity — I build the visual system that makes your brand instantly recognisable.",
        "Diego here — Visual Branding at Playmaker. From your first logo to a full brand overhaul, I create the visual language that represents who you are as an artist.",
        "I'm Diego, your Brand Designer at Playmaker. Merch layouts, press kits, social templates — everything looks consistent, professional, and unmistakably you. What are we building?",
    ],
    "venue-hawk": [
        "I'm Ray B, your Booking Agent at Playmaker. Venues, promoters, show deals, routing — I find the right stages and negotiate the right terms to build your live career.",
        "Ray B here — Global Booking at Playmaker. From local showcases to international tours, I know the venue landscape and the promoters who matter. What are we booking?",
        "I'm Ray B, your Booking Agent at Playmaker. A great live strategy builds your fanbase faster than almost anything else. Let's map out your live game plan.",
    ],
    "tour-commander": [
        "I'm Miles, your Tour Manager at Playmaker. Logistics, production, crew, travel, advancing — I handle everything that has to happen for a show to actually run smoothly.",
        "Miles here — Tour Management at Playmaker. Budget planning, venue advancing, crew hiring, day-of-show operations — I keep tours moving without the chaos. What are we planning?",
        "I'm Miles, your Tour Manager at Playmaker. From the first rehearsal to the last load-out, I make sure every show is executed professionally. What tour are we working on?",
    ],
    "airwave": [
        "I'm Solo, your Radio and Playlist specialist at Playmaker. Getting your music heard by the right programmers, curators, and playlist editors is what I do. What release are we pitching?",
        "Solo here — Radio and Playlist at Playmaker. Commercial radio, college radio, Spotify editorial, Apple Music playlists — I know the gatekeepers and how to reach them.",
        "I'm Solo, your Radio and Playlist advisor at Playmaker. A single playlist placement or radio spin can change your streaming numbers overnight. Let's build a pitching strategy.",
    ],
    "brand-connect": [
        "I'm Nia, your Brand Partnerships specialist at Playmaker. Sponsorships, endorsements, brand deals — I connect your image to brands that make sense and pay well. What's your brand like?",
        "Nia here — Brand Partnerships at Playmaker. From clothing brands to beverage companies to tech sponsors, I find deals that add to your credibility and your income.",
        "I'm Nia, your Brand Partnerships advisor at Playmaker. The right brand deal can fund a tour, boost your visibility, and expand your audience. Let's find your perfect partners.",
    ],
    "merch-empire": [
        "I'm Max, your Merchandise specialist at Playmaker. Design, production, fulfilment, pricing — I build merch operations that actually make money and don't leave you with boxes of unsold stock.",
        "Max here — Merchandise at Playmaker. From your first run of tees to a full product line, I handle the sourcing, production, and strategy to make your merch profitable.",
        "I'm Max, your Merch advisor at Playmaker. Great merch is a revenue stream, a marketing tool, and a fan loyalty system all in one. Let's build yours properly.",
    ],
    "fan-builder": [
        "I'm Aria, your Fan Engagement specialist at Playmaker. Community building, superfan strategy, fan clubs — I turn casual listeners into the loyal core that sustains a long career.",
        "Aria here — Fan Engagement at Playmaker. Discord communities, Patreon, fan newsletters, meet-and-greets — I create the systems that deepen the relationship between you and your fans.",
        "I'm Aria, your Fan Engagement advisor at Playmaker. A thousand true fans beats a million passive listeners every time. Let's build yours intentionally.",
    ],
    "sync-agent": [
        "I'm Sync, your Sync Licensing specialist at Playmaker. TV placements, film scores, advertising, video games — I get your music heard in places that pay well and expand your audience.",
        "Sync here — Sync Licensing at Playmaker. A single ad placement or TV sync can generate more income than months of streaming. I know the music supervisors who make those decisions.",
        "I'm Sync, your Sync Licensing advisor at Playmaker. I'll help you prepare your catalogue for sync, pitch to the right supervisors, and negotiate deals that respect your work.",
    ],
    "global-scout": [
        "I'm Nova, your International Markets specialist at Playmaker. Touring abroad, licensing in new territories, finding international partners — I open doors in markets where your music can grow.",
        "Nova here — International at Playmaker. The global music market is huge and most independent artists ignore 90% of it. I find the territories where your sound has real traction.",
        "I'm Nova, your International advisor at Playmaker. Distribution deals, foreign PRO registration, international touring strategy — I map out your global expansion one market at a time.",
    ],
    "creative-director": [
        "I'm Cree, your Creative Director at Playmaker. Release strategy, aesthetic vision, campaign rollout — I make sure every project you put out has a coherent creative identity that lands.",
        "Cree here — Creative Direction at Playmaker. The gap between a good song and a successful release is usually creative strategy. I close that gap. What are we releasing?",
        "I'm Cree, your Creative Director at Playmaker. From the first single rollout to the album campaign, I design the creative journey that turns a project into a cultural moment.",
    ],
    "data-oracle": [
        "I'm Data, your Analytics specialist at Playmaker. Streaming numbers, audience demographics, DSP insights — I translate the data into decisions that move your career forward.",
        "Data here — Analytics at Playmaker. Spotify for Artists, Apple Music Analytics, social insights — I know what the numbers mean and what you should do about them.",
        "I'm Data, your Analytics advisor at Playmaker. Your streaming data is telling you exactly where your fans are and what they want. Let's listen to it together.",
    ],
    "ar-scout": [
        "I'm Scout, your A&R advisor at Playmaker. Sound development, demo feedback, career positioning — I look at your music through the lens of the industry and help you develop your sound.",
        "Scout here — A&R at Playmaker. I give you the honest feedback that helps you grow, and the strategic advice that helps you find your place in the market.",
        "I'm Scout, your A&R specialist at Playmaker. From refining your sound to identifying what makes you unique in your lane — I help you become the artist you're capable of being.",
    ],
    "producer-connect": [
        "I'm Beat, your Production specialist at Playmaker. Producer connections, beat licensing, co-writing sessions, studio rates — I help you find the right collaborators and get the right deals.",
        "Beat here — Production at Playmaker. Whether you need a producer, a co-writer, or help negotiating a beat lease, I know the landscape and the right people in it.",
        "I'm Beat, your Production advisor at Playmaker. The right producer collaboration can define your sound for years. I help you find that match and structure it properly.",
    ],
    "music-edu": [
        "I'm Prof, your Music Business educator at Playmaker. Industry knowledge, terminology, how deals work, what to watch out for — I make sure you understand the business you're in.",
        "Prof here — Music Business Education at Playmaker. The more you understand how this industry works, the better decisions you make. Ask me anything you've been afraid to ask.",
        "I'm Prof, your Music Business advisor at Playmaker. From royalty splits to label structures to DIY strategies — I explain the music business clearly so you can navigate it confidently.",
    ],
    "collab-connect": [
        "I'm Collab, your Networking specialist at Playmaker. Artist collaborations, features, industry introductions — I help you build the relationships that open doors in this business.",
        "Collab here — Networking and Connections at Playmaker. The right feature, co-write, or industry introduction can change your career trajectory. I help you find and land those opportunities.",
        "I'm Collab, your Networking advisor at Playmaker. A strong network is as valuable as talent in this industry. Let's build yours strategically.",
    ],
    "artist-wellness": [
        "I'm Maya, your Wellness advisor at Playmaker. Mental health, burnout prevention, work-life balance — I make sure the demands of this career don't break the person behind the music.",
        "Maya here — Artist Wellness at Playmaker. The music industry is intense. I help artists build the mental and emotional resilience to sustain a long career without losing themselves.",
        "I'm Maya, your Wellness specialist at Playmaker. Touring stress, creative blocks, financial anxiety, relationship strain — these are real parts of this career. Let's talk about what you're carrying.",
    ],
    "press-monitor": [
        "I'm Press, your Media Monitor at Playmaker. I track every mention, review, and article about you so you always know what's being said and can respond strategically.",
        "Press here — Media Monitoring at Playmaker. Brand sentiment, press coverage, social mentions — I give you a real-time picture of your public narrative.",
        "I'm Press, your Media Monitor at Playmaker. Knowing what the media and public are saying about you is the first step to shaping the story. I keep you informed.",
    ],
    "live-coach": [
        "I'm Coach, your Performance Coach at Playmaker. Stage presence, vocal performance, crowd engagement, nerves — I help you become the performer your recorded music promises you are.",
        "Coach here — Performance Coaching at Playmaker. The gap between a good artist and a great live performer is coachable. I close that gap. What does your live show look like right now?",
        "I'm Coach, your Performance Coach at Playmaker. Whether you're about to play your first show or your hundredth, there's always room to become a more commanding performer.",
    ],
    "audio-quality": [
        "I'm Audio, your Quality Control specialist at Playmaker. Mix feedback, mastering standards, loudness levels, format requirements — I make sure your recordings meet professional release standards.",
        "Audio here — Quality Control at Playmaker. Before anything goes out, I listen with professional ears. Clarity, balance, punch, consistency — I'll tell you exactly where you stand.",
        "I'm Audio, your QC advisor at Playmaker. A bad mix can undermine a great song. I give you the honest technical feedback that helps your music compete at the highest level.",
    ],
    "ai-navigator": [
        "I'm Neo, your AI Tools specialist at Playmaker. From music generation to image creation to workflow automation — I know every AI tool that can save you time and money as an artist.",
        "Neo here — AI Tools and Automation at Playmaker. The AI landscape for musicians is moving fast. I help you find, learn, and use the right tools without the overwhelm.",
        "I'm Neo, your AI Navigator at Playmaker. Whether it's generating stems, creating visuals, writing bios, or automating your schedule — I'll show you exactly which AI tools to use and how.",
    ],
    "royalty-doctor": [
        "I'm Doc, your Royalty Recovery specialist at Playmaker. Unclaimed royalties, black box money, audit discrepancies — if you're owed money somewhere in the system, I find it and recover it.",
        "Doc here — Royalty Recovery at Playmaker. Most artists are owed more than they're collecting. I audit your royalty streams and track down everything that hasn't found its way to you.",
        "I'm Doc, your Royalty Doctor at Playmaker. From international black box funds to DSP underpayments — I've seen every way royalties go missing and I know how to get them back.",
    ],
    "video-director": [
        "I'm Reel, your Music Video strategist at Playmaker. Concept development, director sourcing, budget planning, distribution strategy — I help you make videos that serve your career.",
        "Reel here — Music Video at Playmaker. A great music video is a marketing asset, not just a creative project. I help you plan, produce, and maximise the impact of every video.",
        "I'm Reel, your Video Director advisor at Playmaker. From low-budget performance videos to fully produced visual pieces — I help you get the most out of every dollar you spend on visuals.",
    ],
    "mobile-monetize": [
        "I'm Mo, your Monetization specialist at Playmaker. TikTok Creator Fund, YouTube AdSense, Instagram monetization, Spotify fan tips — I help you activate every revenue stream on every platform.",
        "Mo here — Platform Monetization at Playmaker. Most artists leave significant money on digital platforms because they haven't set up their monetization properly. I fix that.",
        "I'm Mo, your Monetization advisor at Playmaker. From content ID to creator programs to direct-to-fan tools — I map out every platform revenue stream and help you turn them on.",
    ],
    "storefront": [
        "I'm Store, your Fan Store specialist at Playmaker. Direct-to-fan selling, digital downloads, exclusive content, memberships — I help you build a store that your fans actually want to buy from.",
        "Store here — Fan Commerce at Playmaker. Bandcamp, Shopify, Patreon, direct download links — I set up and optimise the systems that let you sell directly to your audience.",
        "I'm Store, your Fan Store advisor at Playmaker. Direct sales have the best margins in the music business. I help you build the storefront and the strategy to make it work.",
    ],
    "content-forge": [
        "I'm Pen, your Content Creation specialist at Playmaker. Bios, press releases, captions, liner notes, EPKs — I write the words that represent you professionally across every platform.",
        "Pen here — Content Creation at Playmaker. From a 150-character Instagram caption to a 1000-word artist bio, I make sure your written presence is as strong as your music.",
        "I'm Pen, your Content advisor at Playmaker. Great content strategy means the right words in the right places at the right time. I handle the writing so you can focus on the music.",
    ],
    "schedule-keeper": [
        "I'm Cal, your Scheduling specialist at Playmaker. Release calendars, content schedules, deadline management, campaign timelines — I keep your career moving at the right pace.",
        "Cal here — Scheduling and Planning at Playmaker. A good release campaign lives or dies on timing. I build the calendars and systems that keep everything on track.",
        "I'm Cal, your Schedule Keeper at Playmaker. From album rollouts to social content plans to studio booking — I map out the timeline and make sure nothing falls through the cracks.",
    ],
    "ink-and-air": [
        "Reed here — Music Publishing at Playmaker. Your songs are assets. I make sure you own them, register them correctly, and get paid every time they're used.",
        "I'm Reed, your Music Publisher at Playmaker. Publishing deals, sync licensing, songwriting royalties — I protect your catalog and maximize what it earns.",
        "Reed, Publishing at Playmaker. Most artists leave serious money on the table because their publishing isn't set up right. Let's fix that.",
    ],
    "live-wire": [
        "Knox here — Booking Agent at Playmaker. Live shows, festivals, touring strategy — I get you on stage and make sure the money is right when you get there.",
        "I'm Knox, your Booking Agent at Playmaker. From local venues to major festivals, I handle the pitches, the contracts, and the performance fees.",
        "Knox, Bookings at Playmaker. A strong live presence builds your fanbase faster than anything else. Let's talk about where you should be performing.",
    ],
    "label-services": [
        "Tommy here — Label Services at Playmaker. Distribution, release planning, DSP delivery, label setup — I make sure your music gets out to the world correctly and on time.",
        "I'm Tommy, your Label Services Manager at Playmaker. From DistroKid to proper label distribution, I handle the infrastructure that gets your music on every platform.",
        "Tommy, Label Services at Playmaker. A great song needs a great release strategy behind it. Let's talk about your next drop and make sure everything is set up right.",
    ],
    "pr-agent": [
        "I'm Quinn, your PR Manager at Playmaker. I write and send personalised outreach emails to press, blogs, podcasts, and magazines — and track every reply so nothing falls through the cracks.",
        "Quinn here — PR at Playmaker. Editorial coverage, interview placements, podcast bookings — I find the right outlets for your music and make the pitch on your behalf.",
        "I'm Quinn, your PR Manager at Playmaker. From Pitchfork to indie blogs, I know who covers your genre and how to reach them. What release are we pushing?",
    ],
    "booking-agent": [
        "I'm Avery, your Booking Agent at Playmaker. I pitch your act to venues, festivals, and promoters — and follow every inquiry through to a confirmed show date.",
        "Avery here — Booking at Playmaker. From local venues to major festivals, I handle the pitches, the negotiations, and the logistics of getting you on stage.",
        "I'm Avery, your Booking Agent at Playmaker. A strong live presence builds your fanbase faster than anything else. Let's map out where you should be performing.",
    ],
    "social-manager": [
        "I'm Riley, your Social Media Manager at Playmaker. I write platform-specific posts, schedule your content calendar, and make sure your online presence actually sounds like you — not a press release.",
        "Riley here — Social at Playmaker. Twitter, Instagram, TikTok, Facebook — I write content that fits each platform's native voice and schedule it at the right times to maximise reach.",
        "I'm Riley, your Social Media Manager at Playmaker. Your music deserves content that connects with real people. I handle the copy, the timing, and the strategy so you can focus on creating.",
    ],
}

# Fallback for any agent not in the dict (shouldn't happen, but just in case)
def _get_greeting(agent: dict) -> str:
    options = _AGENT_GREETINGS.get(agent["id"])
    if options:
        return random.choice(options)
    return f"I'm {agent['name']}, your {agent['title']}. What do you need?"

# ── Mode-specific system prompt suffixes ──────────────────────────────────────
_RULES_SHARED = """
---
EXPERT CALL RULES:
1. You are the expert. Speak with full authority. Never defer, never hedge.
2. Never repeat anything from a previous turn. The artist remembers. Build forward.
3. Use the artist's profile for context. Only mention their genre, stats, or background when directly relevant to their question — never recite it unprompted.
4. CONVERSATION CONTINUITY: If the conversation history contains prior messages, you are RESUMING an existing conversation. Do NOT introduce yourself by name or title. Continue naturally from where you left off. Only introduce yourself on the very first interaction when there is zero prior history.
5. ROUTING — CRITICAL: When a specialist from the AGENT ROSTER is needed, end your response with EXACTLY this sentence and nothing after it:
   "I'll hand you over to [FIRST NAME], our [TITLE]."
   Then STOP completely. Do not ask follow-up questions. Do not continue.
   The exact phrase "hand you over to" triggers the routing system — use it precisely.
   Use the AGENT ROSTER below to choose the right specialist and their exact first name and title.

AGENT ROSTER (routing reference):
Marcus — Artist Manager | Lex — Entertainment Lawyer | Ray — Performance Rights
Cleo — Neighbouring Rights | Finn — Mechanical Royalties | Reed — Music Publisher
Victor — Business Manager | Nadia — Accountant | Jade — Grants & Funding
Mo — Monetization | Tommy — Label Services | Zara — Publicist
Kai — Digital Marketing | Nia — Brand Partnerships | Solo — Radio & Playlist
Aria — Fan Engagement | Max — Merchandise | Store — Fan Store | Pen — Content Creation
Press — Media Monitor | Ray B — Booking Agent | Knox — Booking Agent
Miles — Tour Manager | Coach — Performance Coach | Luna — AI Visuals
Diego — Brand Designer | Cree — Creative Director | Reel — Music Video
Sync — Sync Licensing | Scout — A&R | Beat — Production | Nova — International
Collab — Networking | Prof — Education | Data — Analytics | Audio — Quality Control
Neo — AI Tools | Maya — Wellness | Doc — Royalty Recovery | Cal — Scheduling
Quinn — PR Manager | Avery — Booking Agent | Riley — Social Media Manager
"""

# Voice mode: 150-word hard cap, zero formatting, fast sharp answers
_VOICE_RULES = _RULES_SHARED + """
VOICE MODE — HARD LIMIT: 150 words. Always. No exceptions.
You are speaking on a live call. Be sharp. Be expert. Be complete in 150 words.
ZERO markdown. No asterisks, bullets, dashes, numbers, headers — plain spoken sentences only.
Convert every list to flowing speech: "First... and critically... what you need to know is..."
The artist asks follow-up questions to go deeper. Give the sharp answer, then stop.
"""

# Text mode: full markdown, longer analysis allowed
_TEXT_RULES = _RULES_SHARED + """
TEXT MODE: Use markdown freely. Match depth to question.
Conversational / single topic: 100-200 words.
Analysis / strategy / legal / financial: 300-500 words. Be thorough.
"""

# ── Smart model routing — Haiku for conversation, Sonnet for complexity ────────
MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

_COMPLEX_KEYWORDS = [
    "contract", "clause", "agreement", "deal memo", "deal terms",
    "legal", "lawsuit", "sue", "court", "litigation", "dispute", "arbitration",
    "copyright", "trademark", "patent", "intellectual property", "ip rights",
    "infringement", "breach", "liability", "indemnity",
    "negotiate", "negotiation", "counter-offer",
    "visa", "immigration", "work permit", "o-1", "p-1",
    "tax", "taxes", "audit", "irs", "hmrc", "vat", "withholding",
    "grant application", "grant proposal", "arts council", "funding application",
    "royalty audit", "black box", "unclaimed",
    "license agreement", "sync deal", "publishing deal", "360 deal",
    "master recording", "ownership split", "points", "advance recoupment",
]

def select_model(message: str, tier: str = "") -> tuple[str, int]:
    """
    Returns (model_id, max_tokens) based on artist tier + message complexity.

    GOLD     → always Haiku (fast, cost-effective)
    PLATINUM → Haiku default, Sonnet for complex keywords
    DIAMOND  → always Sonnet (full intelligence every time)
    default  → Haiku
    """
    t = tier.strip().upper()

    if t == "DIAMOND":
        return MODEL_SONNET, 2048

    if t == "GOLD":
        return MODEL_HAIKU, 768

    # PLATINUM and unrecognised tiers: keyword-based routing
    msg_lower = message.lower()
    for kw in _COMPLEX_KEYWORDS:
        if kw in msg_lower:
            return MODEL_SONNET, 2048
    return MODEL_HAIKU, 768

# ── Agent routing detection ────────────────────────────────────────────────────
_ROUTE_LOOKUP: dict[str, dict] = {}
for _a in AGENTS:
    _ROUTE_LOOKUP[_a["name"].lower()]                      = _a
    _ROUTE_LOOKUP[_a["id"]]                                = _a
    _ROUTE_LOOKUP[_a["skill"].replace("maestro-", "")]     = _a
    _ROUTE_LOOKUP[_a["skill"]]                             = _a

# Ordered longest-first so multi-word names ("ray b") match before "ray"
_ROUTE_KEYS = sorted(_ROUTE_LOOKUP.keys(), key=len, reverse=True)

_ROUTING_TRIGGERS = [
    # Primary canonical trigger — automatic handoff, no button in UI
    "hand you over to", "i'll hand you over to", "i will hand you over to",
    # Legacy triggers kept for safety
    "i'm handing you to", "i am handing you to", "handing you to",
    "routing you to", "connecting you with", "switching you to",
    "i'm routing", "i am routing", "let me connect you", "i'll connect you",
    "passing you to", "transfer you to", "handing this to",
    "routed you to", "connected you with", "switched you to",
    "transferred you to", "handed you to", "passed you to",
]

def detect_routing(text: str) -> Optional[dict]:
    """
    Proximity-based routing detection.
    Scans ±150 chars around each trigger phrase for an agent name.
    Returns the target agent (never puppet-master), or None.
    """
    tl = text.lower()

    for trigger in _ROUTING_TRIGGERS:
        pos = tl.find(trigger)
        while pos != -1:
            start  = max(0, pos - 150)
            end    = min(len(tl), pos + len(trigger) + 150)
            window = tl[start:end]
            for key in _ROUTE_KEYS:
                agent = _ROUTE_LOOKUP[key]
                if agent["id"] != "puppet-master" and key in window:
                    return agent
            pos = tl.find(trigger, pos + 1)

    return None

# ── Conversation history helpers ───────────────────────────────────────────────
# Hard caps prevent unbounded token growth across long sessions.
# These are conservative — raise them if artists report losing context.
HISTORY_CAP_VOICE = 10   # turns (5 exchanges) — voice sessions are short
HISTORY_CAP_TEXT  = 20   # turns (10 exchanges) — text sessions can go deeper
HISTORY_CAP_HANDOFF = 20  # turns — full context so receiving agent knows everything discussed

def trim_history(history_list: list, cap: int) -> list:
    """
    Keep the most recent `cap` turns from conversation history.
    Always preserves role integrity (never cuts mid-exchange).
    """
    valid = [t for t in history_list if t.get("role") in ("user", "assistant")]
    if len(valid) <= cap:
        return valid
    trimmed = valid[-cap:]
    # Ensure we start on a user turn (never an orphaned assistant turn)
    while trimmed and trimmed[0].get("role") == "assistant":
        trimmed = trimmed[1:]
    return trimmed

# ── Markdown → clean plain text for TTS ───────────────────────────────────────
def strip_markdown(text: str) -> str:
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_\n]+)_{1,3}', r'\1', text)
    text = re.sub(r'!?\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    return text.strip()

# ── Sentence boundary detector for streaming TTS ──────────────────────────────
_SENT_END = re.compile(
    r'(?<![A-Z][a-z])'
    r'(?<!Mr)(?<!Dr)(?<!Ms)(?<!vs)'
    r'(?<!Mrs)(?<!etc)'
    r'(?<!Jan)(?<!Feb)(?<!Mar)(?<!Apr)'
    r'(?<!Jun)(?<!Jul)(?<!Aug)(?<!Sep)'
    r'(?<!Oct)(?<!Nov)(?<!Dec)'
    r'[.!?]+\s+(?=[A-Z"\'(]|\d)'
)

def split_sentence(buf: str) -> tuple[str, str]:
    """
    Find the last clean sentence boundary in buf.
    Returns (sentence_to_synthesize, remainder).
    Only splits when sentence is ≥ 60 chars to avoid tiny TTS calls.
    """
    for m in reversed(list(_SENT_END.finditer(buf))):
        sentence = buf[:m.end()].strip()
        rest     = buf[m.end():]
        if len(sentence) >= 60:
            return sentence, rest
    return "", buf

# ── Whisper STT ────────────────────────────────────────────────────────────────
_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model

# ── Kokoro TTS ─────────────────────────────────────────────────────────────────
_kokoro = None
_kokoro_available = None
_tts_lock = asyncio.Lock()

def get_kokoro():
    global _kokoro, _kokoro_available
    if _kokoro_available is None:
        onnx_path   = _BASE / "kokoro-v1.0.onnx"
        voices_path = _BASE / "voices-v1.0.bin"
        if not onnx_path.exists() or not voices_path.exists():
            # R-19: print() kept for test_r19 capsys assertion; log for structured output
            print(
                f"[Kokoro] WARNING: Kokoro model files not found at {_BASE}/ "
                "(kokoro-v1.0.onnx and/or voices-v1.0.bin). "
                "TTS will fall back to ElevenLabs. "
                "Expected on Railway (files excluded via .railwayignore); "
                "only an issue if running locally without ElevenLabs configured."
            )
            log.warning("tts_kokoro_missing", extra={
                "event": "tts_kokoro_missing",
                "model_dir": str(_BASE),
                "detail": "Kokoro model files absent; TTS falls back to ElevenLabs. Expected on Railway.",
            })
            _kokoro_available = False
            return None
        try:
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro(str(onnx_path), str(voices_path))
            _kokoro_available = True
            log.info("tts_kokoro_ready", extra={"event": "tts_kokoro_ready"})
        except Exception as e:
            log.error("tts_kokoro_error", extra={"event": "tts_kokoro_error", "error": str(e)})
            _kokoro_available = False
    return _kokoro if _kokoro_available else None

async def synthesize_speech(text: str, voice: str) -> Optional[bytes]:
    """Synthesize text → WAV bytes. Uses Kokoro locally, ElevenLabs on cloud."""
    if not text.strip():
        return None
    kokoro = get_kokoro()
    if not kokoro:
        return await _synthesize_elevenlabs(text, voice)

    cache_key  = hashlib.md5(f"{voice}:1.1:{text}".encode()).hexdigest()
    cache_file = AUDIO_CACHE / f"{cache_key}.wav"
    if cache_file.exists():
        return cache_file.read_bytes()

    async with _tts_lock:
        try:
            import soundfile as sf
            loop = asyncio.get_event_loop()

            def _synth():
                samples, sr = kokoro.create(text, voice=voice, speed=1.1, lang="en-us")
                return samples, sr

            samples, sr = await loop.run_in_executor(None, _synth)

            buf = io.BytesIO()
            sf.write(buf, samples, sr, format='WAV')
            audio_bytes = buf.getvalue()

            cache_file.write_bytes(audio_bytes)
            return audio_bytes
        except Exception as e:
            log.error("tts_kokoro_synth_error", extra={"event": "tts_kokoro_synth_error", "error": str(e)})
            return None

# ── ElevenLabs TTS (cloud fallback) ────────────────────────────────────────────
# Maps Kokoro voice prefix → ElevenLabs pre-made voice ID
_RACHEL  = "21m00Tcm4TlvDq8ikWAM"
_BELLA   = "EXAVITQu4vr4xnSDxMaL"
_ADAM    = "pNInz6obpgDQGcFmaJgB"
_MATILDA = "XrExE9yKIg1WjnnlVkGX"  # warm, international female — South Asian prefix fallback
_LIAM    = "TX3LPaxmHKxFdv7VOQHJ"  # articulate male — Asian male prefix fallback

# ── Per-agent distinct ElevenLabs voice IDs — 16 active agents ────────────────
# Each voice is chosen to match the agent's character: gender, age, accent, personality.
# No two active agents share a voice ID.
_EL_VOICE_MAP = {
    "am_onyx":    "nPczCjzI2devNBz1zQrb",  # Marcus — Brian    (deep, commanding Black male)
    "af_jessica": "21m00Tcm4TlvDq8ikWAM",  # Lex    — Rachel   (clear, professional American female)
    "af_heart":   "XrExE9yKIg1WjnnlVkGX",  # Jade   — Matilda  (warm, international female; closest EL pre-made for South Asian character)
    "am_echo":    "N2lVS1w4EtoT3dr4eOWO",  # Ray    — Callum   (natural, calm American male)
    "bf_emma":    "ThT5KcBeYPX3keUQqHPh",  # Nadia  — Dorothy  (precise British female; fits accountant)
    "am_michael": "yoZ06aMxZJJ28mfd3POQ",  # Mo     — Sam      (raspy, street-smart; fits digital monetization)
    "bm_george":  "IKne3meq5aSn9XLyUdCD",  # Tommy  — Charlie  (Australian/British male; fits label services)
    "af_bella":   "AZnzlk1XvdvUeBnXmlld",  # Zara   — Domi     (strong, energetic American female; fits publicist)
    "am_adam":    "TX3LPaxmHKxFdv7VOQHJ",  # Kai    — Liam     (articulate, tech-clear male; East Asian digital marketing)
    "am_liam":    "TxGEqnHWrfWFTfGW9XjX",  # Solo   — Josh     (smooth, charismatic male; fits radio/playlist)
    "am_fenrir":  "ErXwobaYiN019PkySvjV",  # Ray B  — Antoni   (confident, assured; fits booking agent)
    "bm_lewis":   "GBv7mTt0atIp3Br8iCZE",  # Miles  — Thomas   (calm, organized British male; fits tour manager)
    "af_river":   "jBpfuIE2acCO8z3wKNLl",  # Cree   — Gigi     (young, energetic female; Creative Director)
    "bf_isabella":"EXAVITQu4vr4xnSDxMaL",  # Sync   — Bella    (sophisticated British female; fits sync licensing)
    "af_kore":    "piTKgcLEGmPE4e6mEKli",  # Scout  — Nicole   (perceptive, nuanced female; fits A&R)
    "af_sarah":   "XB0fDUnXU5powFXDhCwa",  # Cal    — Charlotte (young professional female; fits scheduling)
}

_EL_VOICES = {
    # Prefix fallback for non-active agents
    "af": _RACHEL,   # American female
    "bf": _BELLA,    # British female
    "ef": _BELLA,    # European female
    "ff": _BELLA,    # French female
    "hf": _MATILDA,  # South Asian / Hindi female — warm international voice
    "if": _BELLA,    # Italian female
    "jf": _RACHEL,   # Japanese female
    "pf": _BELLA,    # Polish female
    "zf": _RACHEL,   # Chinese female
    "am": _ADAM,     # American male
    "bm": _ADAM,     # British male
    "em": _ADAM,     # European male
    "hm": _ADAM,     # Hindi male
    "im": _ADAM,     # Italian male
    "jm": _LIAM,     # Japanese male — articulate male voice
    "pm": _ADAM,     # Polish male
    "zm": _LIAM,     # Chinese / Asian male — articulate male voice
}

def _pcm_to_wav(pcm_bytes: bytes, sr: int = 24000) -> bytes:
    """Wrap 16-bit PCM bytes in a WAV container."""
    import struct
    channels, sw = 1, 2
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(pcm_bytes)))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, channels, sr,
                          sr * channels * sw, channels * sw, sw * 8))
    buf.write(b"data")
    buf.write(struct.pack("<I", len(pcm_bytes)))
    buf.write(pcm_bytes)
    return buf.getvalue()

_tts_last_error: dict = {}  # temporary diagnostic: stores last ElevenLabs error detail

async def _synthesize_elevenlabs(text: str, voice: str) -> Optional[bytes]:
    """ElevenLabs TTS — returns WAV bytes via PCM output. Cloud fallback for Kokoro."""
    if not ELEVENLABS_API_KEY or not text.strip():
        return None
    # Per-agent voice map first (distinct character voices), then prefix fallback
    voice_id = _EL_VOICE_MAP.get(voice) or _EL_VOICES.get(voice[:2] if len(voice) >= 2 else "am", _ADAM)

    cache_key  = hashlib.md5(f"el:{voice_id}:{text}".encode()).hexdigest()
    cache_file = AUDIO_CACHE / f"{cache_key}.wav"
    if cache_file.exists():
        return cache_file.read_bytes()

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        body = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=30) as cl:
            r = await cl.post(url, json=body, headers=headers)
            log.info("tts_elevenlabs_response", extra={"event": "tts_elevenlabs_response",
                     "status_code": r.status_code, "voice_id": voice_id})
            if r.status_code != 200:
                _tts_last_error["detail"] = f"HTTP {r.status_code}: {r.text[:500]}"
                log.warning("tts_elevenlabs_error", extra={"event": "tts_elevenlabs_error",
                            "status_code": r.status_code, "detail": r.text[:200]})
            r.raise_for_status()
        wav = _pcm_to_wav(r.content, sr=24000)
        cache_file.write_bytes(wav)
        _tts_last_error["detail"] = None
        log.info("tts_elevenlabs_ok", extra={"event": "tts_elevenlabs_ok", "bytes": len(wav)})
        return wav
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        _tts_last_error.setdefault("detail", msg)
        log.error("tts_elevenlabs_exception", extra={"event": "tts_elevenlabs_exception", "error": msg})
        return None

async def tts(text: str, voice: str) -> Optional[bytes]:
    """Strip markdown, then synthesize."""
    clean = strip_markdown(text)
    return await synthesize_speech(clean, voice) if clean else None

# ── System prompt with prompt caching ──────────────────────────────────────────
def load_skill(skill_dir: str) -> str:
    if skill_dir in SKILLS_CACHE:
        return SKILLS_CACHE[skill_dir]
    path = SKILLS_DIR / skill_dir / "SKILL.md"
    return path.read_text() if path.exists() else \
        "You are a world-class music industry specialist. Help the artist with expertise."

def load_artist(artist_id: str = "") -> dict:
    if not artist_id:
        return {}
    if DATABASE_URL:
        return _pg_get(artist_id)
    return _sqlite_get_artist(artist_id)

def load_knowledge() -> str:
    return KNOWLEDGE_BASE.read_text() if KNOWLEDGE_BASE.exists() else ""

def build_system_blocks(agent: dict, artist_id: str = "", voice_mode: bool = True, has_history: bool = False) -> list:
    """
    Returns system prompt as cacheable content blocks.

    Block 1 (cached): SKILL.md + KNOWLEDGE.md  — static, large, 90% cheaper on cache hit.
    Block 2 (live):   Artist profile + mode rules — varies per request, not cached.
    """
    skill_text = load_skill(agent["skill"])
    knowledge  = load_knowledge()
    artist     = load_artist(artist_id)

    static = skill_text
    if knowledge:
        static += f"\n\n---\n# MASTER KNOWLEDGE BASE\n{knowledge}"

    blocks = [
        {
            "type": "text",
            "text": static,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    dynamic_parts = []
    if has_history:
        dynamic_parts.append("RETURNING CONVERSATION: This artist has spoken with you before. Do NOT introduce yourself by name or title. Greet them naturally and continue from where you left off.")
    if artist:
        dynamic_parts.append(f"---\n# CURRENT ARTIST PROFILE\n{json.dumps(artist, indent=2)}")
    dynamic_parts.append(_VOICE_RULES if voice_mode else _TEXT_RULES)
    blocks.append({"type": "text", "text": "\n\n".join(dynamic_parts)})

    return blocks

def build_messages(history_list: list, message: str, cap: int) -> list:
    """
    Build Claude messages array from trimmed history + new message.
    `cap` controls how many historical turns are included.
    """
    msgs = []
    for turn in trim_history(history_list, cap):
        msgs.append({"role": turn["role"], "content": turn["content"]})
    msgs.append({"role": "user", "content": message})
    return msgs

# ── SSE helper ─────────────────────────────────────────────────────────────────
def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

# ── Startup env checks ─────────────────────────────────────────────────────────
def _check_env():
    import re
    sid   = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    phone = os.environ.get("TWILIO_PHONE_NUMBER", "")
    ok = True
    if not sid:
        log.warning("boot_warning", extra={"event": "boot_warning", "key": "TWILIO_ACCOUNT_SID", "detail": "SMS OTP disabled"})
        ok = False
    if not re.fullmatch(r'[0-9a-f]{32}', token.strip().lower()):
        log.warning("boot_warning", extra={"event": "boot_warning", "key": "TWILIO_AUTH_TOKEN",
                    "detail": "invalid format — must be 32 lowercase hex chars; get from console.twilio.com"})
        ok = False
    if not phone:
        log.warning("boot_warning", extra={"event": "boot_warning", "key": "TWILIO_PHONE_NUMBER", "detail": "SMS OTP disabled"})
        ok = False
    if ok:
        log.info("boot_ok", extra={"event": "boot_ok", "key": "TWILIO", "detail": "env vars valid"})
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        log.warning("boot_warning", extra={"event": "boot_warning", "key": "STRIPE_SECRET_KEY", "detail": "billing checkout disabled"})
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        log.warning("boot_warning", extra={"event": "boot_warning", "key": "ANTHROPIC_API_KEY", "detail": "AI agents will fail"})
    else:
        log.info("boot_ok", extra={"event": "boot_ok", "key": "ANTHROPIC_API_KEY", "detail": "present"})

_check_env()


def _check_data_writable() -> None:
    """Warn loudly if /data is not writable — means no Railway volume is mounted."""
    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    probe = data_dir / ".writable_probe"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok")
        probe.unlink()
        print(f"✓  {data_dir} is writable — volume mount OK")
    except OSError as exc:
        print("=" * 60)
        print(f"WARNING: {data_dir} is NOT writable: {exc}")
        print("  All SQLite DBs and OAuth tokens will be lost on redeploy.")
        print("  Action required: Railway dashboard → Service → Volumes → Add")
        print(f"  Volume name: plmkr-data   Mount path: {data_dir}   Size: 1 GB")
        print("=" * 60)


_check_data_writable()

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PLMKR — Playmaker API",
    version="3.0.0",
    description=(
        "AI-powered artist management platform. "
        "Agents handle curator pitching, PR outreach, venue booking, "
        "social scheduling, and weekly reporting — no human copy-paste required.\n\n"
        "**Phases:**\n"
        "- Phase 1: Gmail OAuth + Curator pitch lifecycle\n"
        "- Phase 2: PR contacts + Booking inquiries\n"
        "- Phase 3: Social post scheduling + Weekly reports\n\n"
        "All endpoints require an `artist_id` (the artist's unique identifier in the system)."
    ),
    contact={"name": "PLMKR Support", "email": "getnexusai@gmail.com"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "health",   "description": "Liveness check"},
        {"name": "gmail",    "description": "Gmail OAuth 2.0 connect/disconnect"},
        {"name": "curators", "description": "Curator contact management"},
        {"name": "pitches",  "description": "Curator pitch lifecycle — generate, send, scan, follow-up"},
        {"name": "pr",       "description": "PR contact management and outreach lifecycle"},
        {"name": "booking",  "description": "Booking contact management and inquiry lifecycle"},
        {"name": "social",   "description": "Social post generation, scheduling, and Buffer integration"},
        {"name": "reports",  "description": "Weekly activity reports with AI-generated insights"},
        {"name": "buffer",   "description": "Buffer OAuth 2.0 connect/disconnect"},
        {"name": "agents",   "description": "Agent roster, TTS, conversation, and billing"},
    ],
)

@app.get("/health", tags=["health"], summary="Liveness check")
def health_check():
    """Returns 200 OK when the service is running."""
    return {"status": "ok"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware stack (add_middleware is LIFO — last added executes first) ──────
# Execution order for an incoming request:
#   1. _RequestIDMiddleware  — generates UUID4 request_id, binds to contextvar
#   2. _TimingMiddleware     — records duration, adds Server-Timing header, logs slow requests
#   3. _APIKeyMiddleware     — validates X-API-Key header
#   4. CORSMiddleware        — handles preflight / injects CORS headers

_SLOW_REQUEST_THRESHOLD_MS = 2000.0

class _RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate a UUID4 request_id per request, bind via contextvar, echo as X-Request-ID."""
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        bind_request_id(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class _TimingMiddleware(BaseHTTPMiddleware):
    """Record request duration; add Server-Timing header; warn on slow requests."""
    async def dispatch(self, request: Request, call_next):
        import performance_metrics as _pm
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.1f}"
        route = request.url.path
        _pm.record_request(route, duration_ms)
        if duration_ms >= _SLOW_REQUEST_THRESHOLD_MS:
            from logging_config import get_logger, get_request_id
            get_logger("timing").warning(
                "slow_request",
                extra={
                    "path":        route,
                    "method":      request.method,
                    "duration_ms": round(duration_ms),
                    "status_code": response.status_code,
                    "request_id":  get_request_id(),
                },
            )
        return response


_SKIP_AUTH_PATHS = {"/health", "/api/admin/health/deep", "/docs", "/redoc", "/openapi.json",
                    "/admin/dashboard"}

class _APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _PLMKR_API_KEY:
            return await call_next(request)
        if request.method == "OPTIONS":  # CORS preflight must reach CORSMiddleware unblocked
            return await call_next(request)
        if request.url.path in _SKIP_AUTH_PATHS:
            return await call_next(request)
        key = request.headers.get("X-API-Key", "")
        if not secrets.compare_digest(key, _PLMKR_API_KEY):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing X-API-Key header"},
            )
        return await call_next(request)

app.add_middleware(_APIKeyMiddleware)
app.add_middleware(_TimingMiddleware)
app.add_middleware(_RequestIDMiddleware)

if not _PLMKR_API_KEY:
    print("[AUTH] WARNING: PLMKR_API_KEY is not set — all routes are unauthenticated (dev mode)")


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """Preserve FastAPI's native 422 format; attach request_id for tracing."""
    from logging_config import get_request_id
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "request_id": get_request_id() or str(uuid.uuid4())},
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    """Preserve HTTPException status code and detail; attach request_id for tracing."""
    from logging_config import get_request_id
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": get_request_id() or str(uuid.uuid4())},
    )


@app.exception_handler(Exception)
async def _generic_error_handler(request: Request, exc: Exception):
    """Return a structured error envelope for genuinely unhandled (500-level) exceptions."""
    from logging_config import get_logger, get_request_id
    request_id = get_request_id() or str(uuid.uuid4())
    get_logger("main").error(
        "unhandled_exception",
        extra={"path": str(request.url.path), "error": str(exc)},
        exc_info=exc,
    )
    capture_exception(exc, path=str(request.url.path), request_id=request_id)
    return JSONResponse(
        status_code=500,
        content={"error": type(exc).__name__, "detail": str(exc), "request_id": request_id},
    )

# ── Phase 1 — Pitch service (Gmail, curators, pitch tracking) ─────────────────
from pitch_service import router as _pitch_router, init_pitch_db, init_scheduler
app.include_router(_pitch_router)

# ── Phase 2 — PR & Booking outreach services ───────────────────────────────────
from pr_service import router as _pr_router, init_pr_db
from booking_service import router as _booking_router, init_booking_db
app.include_router(_pr_router)
app.include_router(_booking_router)

# ── Phase 3 — Social scheduling + weekly reports ───────────────────────────────
from social_service import router as _social_router, init_social_db, init_report_scheduler
app.include_router(_social_router)

# ── Phase 4 — iOS backend foundation (push, app config, version check, IAP) ───
from phase4_service import router as _phase4_router, init_phase4_db
app.include_router(_phase4_router)

# ── Admin — Stats + deep health ───────────────────────────────────────────────
from admin_service import router as _admin_router
app.include_router(_admin_router)

# ── Phase 4 — Release campaign orchestration ──────────────────────────────────
from release_service import router as _release_router, init_release_db, execute_all_due_campaign_actions
app.include_router(_release_router)

# Maps agent ID (e.g. "puppet-master") → lowercase first name slug (e.g. "marcus")
_ID_TO_NAME = {a["id"]: a["name"].lower().replace(" ", "-") for a in AGENTS}

class _CloudinaryPhotoMiddleware(BaseHTTPMiddleware):
    """Redirect /static/agents/* to Cloudinary CDN when CLOUDINARY_CLOUD_NAME is set."""
    async def dispatch(self, request, call_next):
        if CLOUDINARY_CLOUD_NAME and request.url.path.startswith("/static/agents/"):
            filename = request.url.path.split("/static/agents/", 1)[1].split("?")[0]
            base = filename.rsplit(".", 1)[0]  # strip .jpg
            name = _ID_TO_NAME.get(base, base)  # resolve agent ID → lowercase name
            cdn = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/image/upload/{name}.jpg"
            return _RedirectResponse(url=cdn, status_code=302)
        return await call_next(request)

app.add_middleware(_CloudinaryPhotoMiddleware)

# ── Conversation history DB ────────────────────────────────────────────────────
DB_PATH  = Path(os.environ.get("DB_PATH", "/data/memory.db"))
_db_lock = asyncio.Lock()

def _ensure_db():
    """Create messages + artists tables on first use (idempotent)."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id TEXT    NOT NULL,
            agent_id  TEXT    NOT NULL,
            role      TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            ts        INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_msg ON messages (artist_id, agent_id, id)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL DEFAULT '{}',
            timezone  TEXT NOT NULL DEFAULT 'UTC'
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] memory.db ready")

def _sqlite_get_artist(artist_id: str) -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    cur  = conn.cursor()
    cur.execute("SELECT data FROM artists WHERE artist_id=?", (artist_id,))
    row  = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def _sqlite_put_artist(artist_id: str, data: dict):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT OR REPLACE INTO artists (artist_id, data) VALUES (?, ?)",
        (artist_id, json.dumps(data))
    )
    conn.commit()
    conn.close()

def _sqlite_all_artists() -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    cur  = conn.cursor()
    cur.execute("SELECT data FROM artists")
    rows = cur.fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]

import threading as _threading

async def _get_message_count(artist_id: str, agent_id: str) -> int:
    """Return saved message count for an artist+agent pair (checks DB directly)."""
    if not artist_id or not agent_id:
        return 0
    def _count():
        conn = sqlite3.connect(str(DB_PATH))
        cur  = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM messages WHERE artist_id=? AND agent_id=?",
            (artist_id, agent_id),
        )
        n = cur.fetchone()[0]
        conn.close()
        return n
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _count)

async def _save_exchange(artist_id: str, agent_id: str, user_msg: str, assistant_msg: str):
    """Persist one user+assistant exchange; prune to 40 most recent rows per pair."""
    if not artist_id or not user_msg.strip() or not assistant_msg.strip():
        return
    loop = asyncio.get_event_loop()
    def _write():
        conn = sqlite3.connect(str(DB_PATH))
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO messages (artist_id, agent_id, role, content) VALUES (?,?,?,?)",
            (artist_id, agent_id, "user", user_msg),
        )
        cur.execute(
            "INSERT INTO messages (artist_id, agent_id, role, content) VALUES (?,?,?,?)",
            (artist_id, agent_id, "assistant", assistant_msg),
        )
        # Keep at most 40 rows (20 exchanges) per artist/agent pair
        cur.execute("""
            DELETE FROM messages
            WHERE  artist_id=? AND agent_id=?
            AND    id NOT IN (
                SELECT id FROM messages
                WHERE  artist_id=? AND agent_id=?
                ORDER  BY id DESC LIMIT 40
            )
        """, (artist_id, agent_id, artist_id, agent_id))
        conn.commit()
        conn.close()
    async with _db_lock:
        await loop.run_in_executor(None, _write)

# ── PostgreSQL artist store (used when DATABASE_URL env var is set) ────────────
# Falls back to flat-file storage when DATABASE_URL is absent (local dev).
def _pg_init():
    import psycopg2
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS artists (
                    artist_id TEXT PRIMARY KEY,
                    data      JSONB NOT NULL DEFAULT '{}'
                )
            """)
    print("[DB] PostgreSQL artists table ready")

def _pg_get(artist_id: str) -> dict:
    import psycopg2
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT data FROM artists WHERE artist_id = %s", (artist_id,))
            row = cur.fetchone()
    return dict(row[0]) if row else {}

def _pg_put(artist_id: str, data: dict):
    import psycopg2, psycopg2.extras
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO artists (artist_id, data) VALUES (%s, %s) "
                "ON CONFLICT (artist_id) DO UPDATE SET data = EXCLUDED.data",
                (artist_id, psycopg2.extras.Json(data))
            )

def _pg_all() -> list[dict]:
    import psycopg2
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT data FROM artists")
            rows = cur.fetchall()
    return [dict(r[0]) for r in rows]

def _init_pg_connection(database_url: str) -> str:
    """Initialise Postgres. Returns effective database_url ('' when absent or on fallback).

    Failure behaviour:
      - DATABASE_URL set + Postgres fails + DB_FAILOVER_TO_SQLITE unset → sys.exit(1)
      - DATABASE_URL set + Postgres fails + DB_FAILOVER_TO_SQLITE=true  → warn + return ""
      - DATABASE_URL unset → SQLite intentional, return "" silently
    """
    if not database_url:
        print("[DB] No DATABASE_URL — using file-based artist storage")
        return ""
    _failover = os.environ.get("DB_FAILOVER_TO_SQLITE", "").lower() == "true"
    print(f"[DB] DATABASE_URL detected (prefix: {database_url[:20]}...) — initialising PostgreSQL")
    try:
        _pg_init()
        return database_url
    except Exception as pg_err:
        if _failover:
            print(f"[DB] WARNING: PostgreSQL init FAILED — DB_FAILOVER_TO_SQLITE=true, using SQLite: {pg_err}")
            return ""
        print(f"[DB] FATAL: PostgreSQL init FAILED: {pg_err}")
        print("[DB] Set DB_FAILOVER_TO_SQLITE=true to allow emergency SQLite fallback.")
        sys.exit(1)


# ── Module-level init ──────────────────────────────────────────────────────────
# Run synchronously at import time so the DB and Kokoro are ready before the
# first request arrives (avoids the 20-35s first-call warmup delay).
_ensure_db()
DATABASE_URL = _init_pg_connection(DATABASE_URL)
_threading.Thread(target=get_kokoro, daemon=True, name="kokoro-warmup").start()
init_pitch_db()
init_scheduler()
init_pr_db()
init_booking_db()
init_social_db()
init_report_scheduler()
init_release_db()
init_phase4_db()

# Wire campaign executor into scheduler (every 1h)
# Runs in both "true" (live) and "dry_run" modes; execute_all_due_campaign_actions()
# checks _SCHEDULER_DRY_RUN internally and logs instead of firing side effects.
_SCHEDULER_ENABLED_FLAG = os.environ.get("SCHEDULER_ENABLED", "").lower() in ("true", "dry_run")
if _SCHEDULER_ENABLED_FLAG:
    try:
        from pitch_service import _scheduler as _pitch_sched
        if _pitch_sched and _pitch_sched.running:
            _pitch_sched.add_job(
                execute_all_due_campaign_actions,
                "interval",
                hours=1,
                id="campaign_executor",
                replace_existing=True,
                coalesce=True,
                misfire_grace_time=120,
            )
            print("[Release] Campaign executor scheduled — every 1h")
    except Exception as _sched_err:
        print(f"[Release] Campaign scheduler hook failed: {_sched_err}")
print("[INIT] DB ready, Kokoro warmup thread started, pitch/PR/booking/social services initialised")

@app.get("/api/agents")
async def list_agents():
    return {"agents": AGENTS}

@app.get("/api/artist")
async def get_artist(artist_id: str = ""):
    return load_artist(artist_id)

@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), request: Request = None):
    try:
        filename = audio.filename or "voice.m4a"
        ext      = (os.path.splitext(filename)[1] or ".m4a").lower()

        if ext not in _ALLOWED_AUDIO_EXTS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format '{ext}'. Allowed: {sorted(_ALLOWED_AUDIO_EXTS)}",
            )

        # Reject oversized uploads before reading the body when Content-Length is present.
        cl = audio.headers.get("content-length") if audio.headers else None
        if cl is not None and int(cl) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit",
            )

        data = await audio.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit",
            )

        model = get_whisper()
        print(f"[TRANSCRIBE] received {len(data)} bytes, filename={filename}, ext={ext}")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(data)
            tmp = f.name
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: model.transcribe(tmp))
        os.unlink(tmp)
        text = result["text"].strip()
        print(f"[TRANSCRIBE] result: {repr(text)}")
        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TRANSCRIBE] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/greet")
async def greet(agent_id: str = Form(...), tts_on: str = Form(default="true", alias="tts")):
    """
    Returns the agent's opening line when an artist enters a chat.

    ALL agents now use static rotating greetings — zero API calls.
    This was the single biggest source of unnecessary token spend during testing.
    Each agent has 3–5 handcrafted variants; Marcus has 5.
    """
    agent = AGENTS_BY_ID.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    greeting_text = _get_greeting(agent)

    audio_b64 = None
    if tts_on.lower() == "true":
        audio_bytes = await tts(greeting_text, agent["voice"])
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode()

    return {"reply": greeting_text, "audio": audio_b64}


@app.post("/api/handoff")
async def handoff(
    agent_id:      str = Form(...),
    history:       str = Form(default="[]"),
    tts_on:        str = Form(default="true", alias="tts"),
    artist_id:     str = Form(default=""),
    from_agent_id: str = Form(default="puppet-master"),
):
    """
    New agent delivers a warm personalised greeting after Marcus routes to them.

    Receiving agent gets full conversation context (HISTORY_CAP_HANDOFF turns)
    so they can greet the artist by name and reference what was discussed.
    The from_agent_id param makes the handoff prompt dynamic (not hardcoded to Marcus).

    The greeting prompt now instructs the agent to use the artist's name and
    reference something specific from the recent conversation. This fixes the
    generic "I'm routing you to X" wording from the previous version.
    """
    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI unavailable: ANTHROPIC_API_KEY not configured")
    agent = AGENTS_BY_ID.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        history_list = json.loads(history)
    except Exception:
        history_list = []

    artist      = load_artist(artist_id)
    artist_name = artist.get("artist_name", "you")
    do_tts      = tts_on.lower() == "true"

    from_agent  = AGENTS_BY_ID.get(from_agent_id)
    from_name   = from_agent["name"] if from_agent else "Marcus"

    # Full conversation history — receiving agent gets complete context
    trimmed_history = trim_history(history_list, HISTORY_CAP_HANDOFF)

    # Pass has_history so receiving agent doesn't intro themselves when context exists
    system_blocks = build_system_blocks(agent, artist_id=artist_id, voice_mode=do_tts, has_history=bool(trimmed_history))

    # Build rich handoff context: last 3 user messages (topic) + any actions already taken by from_agent
    user_msgs    = [t["content"] for t in trimmed_history if t.get("role") == "user"]
    agent_msgs   = [t["content"] for t in trimmed_history if t.get("role") == "assistant"]
    topic        = " | ".join(user_msgs[-3:])[:350] if user_msgs else ""
    _action_kws  = ["i sent", "i emailed", "i pitched", "i submitted", "i scheduled",
                    "i booked", "i drafted", "i found", "i created", "i looked", "i reviewed"]
    actions_done = next(
        (m[:200] for m in reversed(agent_msgs[-5:])
         if any(w in m.lower() for w in _action_kws)),
        ""
    )

    context_block = ""
    if topic:
        context_block += f"What the artist needs: {topic}\n"
    if actions_done:
        context_block += f"Actions {from_name} already took: {actions_done}\n"

    handoff_prompt = (
        f"{from_name} just handed {artist_name} directly to you. Full context is above.\n"
        f"{context_block}"
        f'Open with EXACTLY this pattern — fill in the specific issue from context:\n'
        f'"{artist_name}, {from_name} filled me in — I understand you need help with [specific issue]. '
        f'Let me take it from here."\n'
        f"One sentence only. No preamble. No filler. Sound like the expert you are."
    )

    messages = []
    for turn in trimmed_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": handoff_prompt})

    try:
        resp = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=120,
            system=system_blocks,
            messages=messages,
            extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        )
        reply = resp.content[0].text
    except Exception:
        reply = f"Hey {artist_name}, I'm {agent['name']} — your {agent['title']}. Marcus filled me in. Let's get straight to it — what do you need?"

    audio_b64 = None
    if do_tts:
        audio_bytes = await tts(reply, agent["voice"])
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode()

    return {"reply": reply, "audio": audio_b64}

class ChatStreamRequest(BaseModel):
    agent_id:  str
    message:   str
    artist_id: str    = ""
    history:   str    = "[]"   # JSON-encoded array
    tts:       bool   = True

@app.post("/api/chat_stream")
async def chat_stream(req: ChatStreamRequest):
    agent_id  = req.agent_id
    message   = req.message
    artist_id = req.artist_id
    history   = req.history
    tts_on    = "true" if req.tts else "false"
    """
    Streaming endpoint. Yields SSE events:
      {type:"text",  text:"..."}           — sentence of text as it arrives
      {type:"audio", audio:"<b64 wav>"}    — synthesized audio for that sentence
      {type:"route", agent_id, agent_name} — if Marcus routes to another agent
      {type:"done",  full_text:"..."}      — final full response text
      {type:"error", message:"..."}        — on failure

    History is trimmed before each call to prevent unbounded token growth.
    Voice sessions use a tighter cap than text sessions.
    """
    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI unavailable: ANTHROPIC_API_KEY not configured")
    agent = AGENTS_BY_ID.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    skill_path = SKILLS_DIR / agent["skill"] / "SKILL.md"
    print(f"\n[AGENT] {agent['name']} ({agent_id}) | SKILL: {'OK' if skill_path.exists() else 'MISSING'}")

    try:
        history_list = json.loads(history)
    except Exception:
        history_list = []

    do_tts = tts_on.lower() == "true"

    if message == "__greet__":
        greeting_text = _get_greeting(agent)
        print(f"[GREET] {agent['name']} — static greeting ({len(greeting_text)} chars)")
        async def _static_greet():
            yield sse({"type": "text",  "text": greeting_text})
            yield sse({"type": "done",  "full_text": greeting_text})
        return StreamingResponse(
            _static_greet(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        has_history = len(history_list) > 0

    system_blocks = build_system_blocks(agent, artist_id=artist_id, voice_mode=do_tts, has_history=has_history)

    # Use tighter history cap for voice (faster, cheaper); wider for text (more context)
    history_cap = HISTORY_CAP_VOICE if do_tts else HISTORY_CAP_TEXT
    messages    = build_messages(history_list, message, cap=history_cap)

    voice         = agent["voice"]
    tier          = load_artist(artist_id).get("tier", "")
    model, max_tokens = select_model(message, tier)

    # Voice mode: hard cap at 300 tokens (~150 words) regardless of model
    if do_tts:
        max_tokens = 300

    print(f"[ROUTE] {agent['name']} | tier={tier or 'default'} | model={model.split('-')[1]} | voice={do_tts} | history={len(messages)-1} turns | max_tok={max_tokens}")

    async def generate():
        full_text = ""

        tts_in  = asyncio.Queue()
        evt_out = asyncio.Queue()

        async def _claude():
            nonlocal full_text
            buf = ""
            route_cut = False
            try:
                async with async_client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_blocks,
                    messages=messages,
                    extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
                ) as stream:
                    async for chunk in stream.text_stream:
                        full_text += chunk
                        buf       += chunk
                        while True:
                            sentence, buf = split_sentence(buf)
                            if not sentence:
                                break
                            await evt_out.put(("text", sentence))
                            if do_tts:
                                await tts_in.put(sentence)
                            if detect_routing(sentence):
                                route_cut = True
                                break
                        if route_cut:
                            break

                if not route_cut:
                    remainder = buf.strip()
                    if remainder:
                        await evt_out.put(("text", remainder))
                        if do_tts:
                            await tts_in.put(remainder)

            except Exception as e:
                await evt_out.put(("error", str(e)))
            finally:
                await tts_in.put(None)

        async def _tts_worker():
            # Eager synthesis: start each sentence's TTS task as soon as it arrives
            # so sentence N+1 queues on the lock while sentence N is still transmitting.
            task_q = asyncio.Queue()
            first  = True

            async def _submit():
                nonlocal first
                while True:
                    sentence = await tts_in.get()
                    if sentence is None:
                        await task_q.put(None)
                        return
                    if first:
                        await evt_out.put(("status", "Generating voice…"))
                        first = False
                    # Create the synthesis task immediately — it queues behind the
                    # TTS lock so N+1 starts the moment N finishes, eliminating the gap.
                    task = asyncio.create_task(tts(sentence, voice))
                    await task_q.put(task)

            asyncio.create_task(_submit())
            while True:
                item = await task_q.get()
                if item is None:
                    break
                audio_bytes = await item
                if audio_bytes:
                    await evt_out.put(("audio", audio_bytes))
            await evt_out.put(None)

        asyncio.create_task(_claude())
        if do_tts:
            asyncio.create_task(_tts_worker())
        else:
            async def _no_tts_closer():
                while True:
                    s = await tts_in.get()
                    if s is None:
                        break
                await evt_out.put(None)
            asyncio.create_task(_no_tts_closer())

        while True:
            item = await evt_out.get()
            if item is None:
                break
            evt_type, data = item
            if evt_type == "text":
                yield sse({"type": "text", "text": data})
            elif evt_type == "audio":
                yield sse({"type": "audio", "audio": base64.b64encode(data).decode()})
            elif evt_type == "status":
                yield sse({"type": "status", "text": data})
            elif evt_type == "error":
                yield sse({"type": "error", "message": data})
                break

        route = detect_routing(full_text)
        if route:
            slug = route["name"].lower().replace(" ", "-")
            yield sse({
                "type":        "route",
                "agent_id":    route["id"],
                "agent_name":  route["name"],
                "agent_title": route["title"],
                "agent_voice": route["voice"],
                "agent_slug":  slug,
            })
        yield sse({"type": "done", "full_text": full_text})

        # Persist exchange to history DB (skip greeting pings)
        if full_text and message != "__greet__":
            asyncio.create_task(_save_exchange(artist_id, agent_id, message, full_text))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/api/tts")
async def tts_endpoint(text: str, voice: str = "am_michael"):
    audio_bytes = await tts(text, voice)
    if audio_bytes:
        return Response(content=audio_bytes, media_type="audio/wav")
    return JSONResponse({"error": "TTS unavailable"}, status_code=503)

_cancelled_calls: set = set()  # call_ids cancelled mid-flight; checked before returning audio

class TtsSynthRequest(BaseModel):
    text:    str
    voice:   str = "am_onyx"
    call_id: str = ""

class TtsCancelRequest(BaseModel):
    call_id: str

@app.post("/api/tts/cancel")
async def tts_cancel(req: TtsCancelRequest):
    """Mark a call as ended so any in-flight /api/tts/synth for that call returns null."""
    if req.call_id:
        _cancelled_calls.add(req.call_id)
    return {"cancelled": req.call_id}

@app.post("/api/tts/synth")
async def tts_synth(req: TtsSynthRequest):
    """Synthesize text → base64 WAV. Used by app to bypass SSE buffering."""
    if req.call_id and req.call_id in _cancelled_calls:
        _cancelled_calls.discard(req.call_id)
        return JSONResponse({"audio": None, "cancelled": True}, status_code=200)
    _tts_last_error.clear()
    audio_bytes = await tts(req.text, req.voice)
    # Check again — call may have ended while synthesis was running
    if req.call_id and req.call_id in _cancelled_calls:
        _cancelled_calls.discard(req.call_id)
        return JSONResponse({"audio": None, "cancelled": True}, status_code=200)
    if audio_bytes:
        return {"audio": base64.b64encode(audio_bytes).decode()}
    detail = _tts_last_error.get("detail", "unknown")
    return JSONResponse({"audio": None, "error": "TTS unavailable", "detail": detail}, status_code=503)

@app.get("/api/tts/status")
async def tts_status():
    """Returns whether TTS is ready. True if Kokoro loaded OR ElevenLabs key present."""
    kokoro_ready = _kokoro_available is True
    el_ready     = bool(ELEVENLABS_API_KEY)
    return {"ready": kokoro_ready or el_ready, "engine": "kokoro" if kokoro_ready else ("elevenlabs" if el_ready else "none")}

@app.get("/api/health")
async def api_health():
    tts_engine = "kokoro" if get_kokoro() else ("elevenlabs" if ELEVENLABS_API_KEY else "none")
    return {"status": "ok", "version": "2.2.1", "tts": tts_engine, "agents": len(AGENTS)}

app.mount("/static", StaticFiles(directory=str(_BASE / "static"), html=True), name="static")


# ── Artist save ────────────────────────────────────────────────────────────────
from pydantic import BaseModel

class ArtistProfile(BaseModel):
    artist_id: str
    name: str
    country: str = ""
    genres: list[str] = []
    monthly_listeners: str = ""
    tier: str = "Gold"
    onboarded: bool = False
    bio: str = ""
    photo: Optional[str] = None

@app.post("/api/artist/save")
async def save_artist(profile: ArtistProfile):
    try:
        existing = load_artist(profile.artist_id)

        # Map app profile fields to the store format Maestro expects
        existing.update({
            "artist_id":         profile.artist_id,
            "artist_name":       profile.name,
            "country":           profile.country,
            "genres":            profile.genres,
            "monthly_listeners": profile.monthly_listeners,
            "tier":              profile.tier,
            "onboarded":         profile.onboarded,
            "bio":               profile.bio,
            "photo":             profile.photo,
        })

        _save_artist_file(profile.artist_id, existing)
        print(f"[ARTIST] Saved profile for {profile.name} ({profile.artist_id})")
        return {"status": "ok", "artist_id": profile.artist_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Billing upgrade ────────────────────────────────────────────────────────────
class BillingUpgrade(BaseModel):
    artist_id: str
    tier: str

@app.post("/api/billing/upgrade")
async def billing_upgrade(payload: BillingUpgrade):
    try:
        if payload.tier not in ("Starter", "Gold", "Platinum", "Diamond"):
            raise HTTPException(status_code=400, detail="Invalid tier")

        existing = load_artist(payload.artist_id)
        existing["artist_id"] = payload.artist_id
        existing["tier"] = payload.tier
        _save_artist_file(payload.artist_id, existing)
        print(f"[BILLING] {payload.artist_id} upgraded to {payload.tier}")
        return {"status": "ok", "tier": payload.tier}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Conversation history read ──────────────────────────────────────────────────
@app.get("/api/history")
async def get_history(artist_id: str, agent_id: str):
    try:
        if not DB_PATH.exists():
            return {"history": []}
        conn = sqlite3.connect(str(DB_PATH))
        cur  = conn.cursor()
        cur.execute(
            "SELECT role, content FROM messages WHERE artist_id=? AND agent_id=? ORDER BY id ASC LIMIT 40",
            (artist_id, agent_id)
        )
        rows = cur.fetchall()
        conn.close()
        return {"history": [{"role": r[0], "content": r[1]} for r in rows]}
    except Exception as e:
        print(f"[HISTORY] error: {e}")
        return {"history": []}


# ── Artist lookup by name ──────────────────────────────────────────────────────
@app.get("/api/artist/lookup")
async def lookup_artist(name: str):
    """Find existing artist profile by name (case-insensitive) across all artist profiles."""
    try:
        target = name.lower().strip()
        if DATABASE_URL:
            profiles = _pg_all()
        else:
            profiles = _sqlite_all_artists()
        for profile in profiles:
            if profile.get("artist_name", "").lower() == target:
                return {
                    "found": True,
                    "artist_id": profile.get("artist_id"),
                    "name": profile.get("artist_name"),
                    "tier": profile.get("tier", "Gold"),
                    "genres": profile.get("genres", []),
                    "country": profile.get("country", ""),
                    "monthly_listeners": profile.get("monthly_listeners", ""),
                    "bio": profile.get("bio", ""),
                    "photo": profile.get("photo", None),
                    "onboarded": profile.get("onboarded", False),
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


# ── SMS OTP auth ───────────────────────────────────────────────────────────────
# In-memory store: { normalized_phone: { "otp": "123456", "expires": float } }
_otp_store: dict = {}
OTP_EXPIRY_SECONDS = 600  # 10 minutes


def _normalize_phone(raw: str) -> str:
    """Strip everything except digits, then prepend +."""
    digits = re.sub(r'\D', '', raw.strip())
    return '+' + digits


def _clean_otp_store():
    now = time.time()
    expired = [k for k, v in _otp_store.items() if v["expires"] < now]
    for k in expired:
        del _otp_store[k]


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    code: str


@app.post("/api/auth/send-otp")
async def send_otp(payload: SendOtpRequest):
    """Send a 6-digit OTP via Twilio SMS. Requires TWILIO_* env vars."""
    try:
        _clean_otp_store()

        phone = _normalize_phone(payload.phone)
        if len(phone) < 8:
            raise HTTPException(status_code=400, detail="Invalid phone number")

        # R-17 dev bypass: skip Twilio and store a fixed dev code
        if SMS_OTP_DEV_BYPASS:
            dev_otp = "000000"
            _otp_store[phone] = {"otp": dev_otp, "expires": time.time() + OTP_EXPIRY_SECONDS}
            log.warning("boot_warning", extra={
                "event":  "boot_warning",
                "key":    "SMS_OTP_DEV_BYPASS",
                "detail": f"dev OTP 000000 stored for ...{phone[-4:]} without SMS send",
            })
            return {"status": "ok", "message": "Dev bypass — code is 000000"}

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            raise HTTPException(status_code=503, detail="SMS service not configured — set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")

        # Strip whitespace — Railway env vars can have trailing newlines/spaces
        auth_token  = (auth_token  or "").strip()
        account_sid = (account_sid or "").strip()
        from_number = (from_number or "").strip()

        # Validate auth token format BEFORE storing OTP (R-17 fix: was after)
        if not (auth_token and len(auth_token) == 32 and re.fullmatch(r"[0-9a-f]+", auth_token.lower())):
            raise HTTPException(
                status_code=503,
                detail=f"SMS not configured — TWILIO_AUTH_TOKEN must be exactly 32 lowercase hex characters (got {len(auth_token)} chars). Set the correct token in Railway env vars."
            )

        otp = str(secrets.randbelow(1000000)).zfill(6)
        _otp_store[phone] = {"otp": otp, "expires": time.time() + OTP_EXPIRY_SECONDS}

        from twilio.rest import Client as TwilioClient
        twilio = TwilioClient(account_sid, auth_token)
        twilio.messages.create(
            body=f"Your PLMKR code is {otp}. Valid for 10 minutes.",
            from_=from_number,
            to=phone,
        )

        print(f"[OTP] Sent to ...{phone[-4:]}")
        return {"status": "ok", "message": "Code sent"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[OTP] Send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/verify-otp")
async def verify_otp(payload: VerifyOtpRequest):
    """Verify a 6-digit OTP. Consumes the code on success."""
    phone = _normalize_phone(payload.phone)
    entry = _otp_store.get(phone)

    if not entry:
        return {"valid": False, "reason": "No code found for this number. Please request a new code."}

    if time.time() > entry["expires"]:
        del _otp_store[phone]
        return {"valid": False, "reason": "Code expired. Please request a new one."}

    if entry["otp"] != payload.code.strip():
        return {"valid": False, "reason": "Incorrect code. Try again."}

    del _otp_store[phone]
    return {"valid": True}


# ── Push notifications ─────────────────────────────────────────────────────────
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class RegisterTokenRequest(BaseModel):
    artist_id: str
    push_token: str


class SendNotificationRequest(BaseModel):
    artist_id: str
    title: str
    body: str
    agent_id: str = ""
    data: dict = {}


def _load_artist_file(artist_id: str) -> tuple:
    """Return (artist_id, data). artist_id is passed through as the key for _save_artist_file."""
    if DATABASE_URL:
        return artist_id, _pg_get(artist_id)
    return artist_id, _sqlite_get_artist(artist_id)


def _save_artist_file(path_or_id, data: dict):
    if DATABASE_URL:
        _pg_put(data["artist_id"], data)
        return
    _sqlite_put_artist(data["artist_id"], data)


@app.post("/api/notifications/register")
async def register_push_token(payload: RegisterTokenRequest):
    """Save Expo push token to the artist's JSON file."""
    try:
        path, data = _load_artist_file(payload.artist_id)
        data["push_token"] = payload.push_token
        _save_artist_file(path, data)
        print(f"[PUSH] Registered token for {payload.artist_id}")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/send")
async def send_notification(payload: SendNotificationRequest):
    """Send a push notification to an artist via Expo push API and store in history."""
    try:
        path, data = _load_artist_file(payload.artist_id)
        push_token = data.get("push_token", "")

        result = {"status": "ok", "delivered": False, "artist_id": payload.artist_id}

        if push_token:
            message = {
                "to":    push_token,
                "title": payload.title,
                "body":  payload.body,
                "sound": "default",
                "data":  payload.data or {},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    EXPO_PUSH_URL,
                    json=message,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )
            resp_data  = resp.json()
            data_field = resp_data.get("data", {})
            # Single send returns dict; batch returns list — handle both
            if isinstance(data_field, list):
                expo_status = data_field[0].get("status", "unknown") if data_field else "unknown"
            else:
                expo_status = data_field.get("status", "unknown")
            result["delivered"] = expo_status == "ok"
            result["expo_status"] = expo_status
            print(f"[PUSH] Sent to {payload.artist_id}: {expo_status}")
        else:
            result["note"] = "No push token registered for this artist"
            print(f"[PUSH] No token for {payload.artist_id} — notification stored only")

        # Always append to notification history regardless of delivery
        notif_entry = {
            "id":       hashlib.md5(f"{payload.artist_id}{payload.title}{time.time()}".encode()).hexdigest()[:12],
            "type":     "agent" if payload.agent_id else "system",
            "agent_id": payload.agent_id,
            "title":    payload.title,
            "body":     payload.body,
            "sent_at":  time.time(),
            "read":     False,
        }
        data.setdefault("notifications", []).insert(0, notif_entry)
        # Keep last 100 notifications
        data["notifications"] = data["notifications"][:100]
        _save_artist_file(path, data)

        return result

    except Exception as e:
        print(f"[PUSH] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notifications/{artist_id}")
async def get_notifications(artist_id: str):
    """Return the artist's notification history from their JSON file."""
    try:
        _, data = _load_artist_file(artist_id)
        return {"notifications": data.get("notifications", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Stripe billing ─────────────────────────────────────────────────────────────
import stripe as stripe_lib


STRIPE_SECRET_KEY        = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET    = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_DEV_ALLOW_UNSIGNED = os.environ.get("STRIPE_DEV_ALLOW_UNSIGNED", "").lower() == "true"
STRIPE_AVAILABLE         = bool(STRIPE_SECRET_KEY)
APP_BASE_URL             = os.environ.get("APP_BASE_URL") or None   # R-11: None if unset
_RAILWAY_ENVIRONMENT    = os.environ.get("RAILWAY_ENVIRONMENT", "")

# Refuse to start if the dev bypass is active in a Railway production environment.
# STRIPE_DEV_ALLOW_UNSIGNED skips webhook signature verification — safe in local dev,
# catastrophic if left on in production (accepts forged events from anyone).
_on_railway = bool(_RAILWAY_ENVIRONMENT)

# R-11: hard-fail in production if APP_BASE_URL is unset; fall back in dev.
if APP_BASE_URL is None:
    if _on_railway:
        print("=" * 60)
        print("FATAL: APP_BASE_URL is not set on Railway.")
        print("  OAuth redirect URIs, billing links, and audio URLs require")
        print("  a public HTTPS base URL. Set APP_BASE_URL in Railway Variables:")
        print("  e.g. https://your-service.up.railway.app")
        print("=" * 60)
        import sys
        sys.exit(1)
    else:
        APP_BASE_URL = "http://localhost:8000"
        log.warning("boot_warning", extra={
            "event":  "boot_warning",
            "key":    "APP_BASE_URL",
            "detail": "unset — falling back to http://localhost:8000 (set before deploying to Railway)",
        })

if _on_railway and STRIPE_DEV_ALLOW_UNSIGNED:
    print("=" * 60)
    print("FATAL: STRIPE_DEV_ALLOW_UNSIGNED=true detected on Railway.")
    print(f"  RAILWAY_ENVIRONMENT={_RAILWAY_ENVIRONMENT!r}")
    print("  This bypasses webhook signature verification in production.")
    print("  Unset STRIPE_DEV_ALLOW_UNSIGNED before deploying.")
    print("=" * 60)
    import sys
    sys.exit(1)
if STRIPE_AVAILABLE:
    stripe_lib.api_key = STRIPE_SECRET_KEY

# R-17: SMS_OTP_DEV_BYPASS allows send-otp to succeed in local dev without real Twilio.
SMS_OTP_DEV_BYPASS = os.environ.get("SMS_OTP_DEV_BYPASS", "").lower() == "true"
if _on_railway and SMS_OTP_DEV_BYPASS:
    print("=" * 60)
    print("FATAL: SMS_OTP_DEV_BYPASS=true detected on Railway.")
    print(f"  RAILWAY_ENVIRONMENT={_RAILWAY_ENVIRONMENT!r}")
    print("  This bypasses SMS verification in production.")
    print("  Unset SMS_OTP_DEV_BYPASS before deploying.")
    print("=" * 60)
    import sys
    sys.exit(1)
if SMS_OTP_DEV_BYPASS:
    log.warning("boot_warning", extra={
        "event":  "boot_warning",
        "key":    "SMS_OTP_DEV_BYPASS",
        "detail": "OTP bypass active — send-otp stores dev code without calling Twilio",
    })

if not STRIPE_WEBHOOK_SECRET and not STRIPE_DEV_ALLOW_UNSIGNED:
    print("[STRIPE] WARNING: STRIPE_WEBHOOK_SECRET not set and STRIPE_DEV_ALLOW_UNSIGNED not enabled — "
          "webhook endpoint will reject all incoming events with HTTP 400")


def _verify_stripe_event(body: bytes, sig_header: str, webhook_secret: str, dev_allow_unsigned: bool):
    """Verify a Stripe webhook event. Raises HTTPException on failure.

    Production: webhook_secret must be set — unsigned events are rejected.
    Dev only:   set STRIPE_DEV_ALLOW_UNSIGNED=true to accept unsigned events.
    """
    if webhook_secret:
        return stripe_lib.Webhook.construct_event(body, sig_header, webhook_secret)
    if dev_allow_unsigned:
        print("[STRIPE] WARNING: accepting unsigned webhook event — STRIPE_DEV_ALLOW_UNSIGNED=true")
        return stripe_lib.Event.construct_from(json.loads(body), stripe_lib.api_key)
    raise HTTPException(
        status_code=400,
        detail="Webhook signature verification required — set STRIPE_WEBHOOK_SECRET",
    )

TIER_PRICES = {
    "Starter":  2900,    # $29.00 in cents
    "Gold":     4900,    # $49.00
    "Platinum": 9900,    # $99.00
    "Diamond":  19900,   # $199.00
}

# Pre-created Stripe Price IDs (recurring monthly, test mode)
PRICE_IDS = {
    "Starter":  "price_1TC7wsKcfMmE6BHPtCwDbkWD",
    "Gold":     "price_1TC7xHKcfMmE6BHPqa0aU1f2",
    "Platinum": "price_1TC7y0KcfMmE6BHPEzJ55j7E",
    "Diamond":  "price_1TC7ySKcfMmE6BHPvwN08fki",
}

class CheckoutRequest(BaseModel):
    artist_id: str
    tier: str

def _add_billing_history(data: dict, tier: str, amount: float):
    entry = {
        "id":     f"stripe_{int(time.time())}",
        "date":   time.strftime("%b %-d, %Y"),
        "amount": amount,
        "tier":   tier,
        "status": "paid",
    }
    data.setdefault("billing_history", []).insert(0, entry)
    data["billing_history"] = data["billing_history"][:50]

@app.post("/api/billing/create-checkout")
async def create_checkout(payload: CheckoutRequest):
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing unavailable — STRIPE_SECRET_KEY not set")
    if payload.tier not in PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": PRICE_IDS[payload.tier],
                "quantity": 1,
            }],
            client_reference_id=payload.artist_id,
            metadata={"artist_id": payload.artist_id, "tier": payload.tier},
            success_url=f"{APP_BASE_URL}/static/billing-success.html",
            cancel_url=f"{APP_BASE_URL}/static/billing-cancel.html",
        )
        print(f"[STRIPE] checkout session created for {payload.artist_id} → {payload.tier}")
        return {"url": session.url, "session_id": session.id}
    except stripe_lib.error.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e.user_message or e))

@app.post("/api/billing/webhook")
async def billing_webhook(request: Request):
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Billing unavailable")
    body       = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:

        event = _verify_stripe_event(body, sig_header, STRIPE_WEBHOOK_SECRET, STRIPE_DEV_ALLOW_UNSIGNED)


    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    etype = event["type"]
    data  = event["data"]["object"]
    print(f"[STRIPE] webhook: {etype}")

    if etype == "checkout.session.completed":
        artist_id = data.get("client_reference_id") or data.get("metadata", {}).get("artist_id", "")
        tier      = data.get("metadata", {}).get("tier", "")
        if artist_id and tier and tier in TIER_PRICES:
            path, adata = _load_artist_file(artist_id)
            adata["tier"]                = tier
            adata["subscription_id"]     = data.get("subscription", "")
            adata["subscription_status"] = "active"
            _add_billing_history(adata, tier, TIER_PRICES[tier] / 100)
            _save_artist_file(path, adata)
            print(f"[STRIPE] {artist_id} → {tier} active")

    elif etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        sub_id = data.get("id", "")
        status = data.get("status", "")
        if DATABASE_URL:
            all_artists = _pg_all()
        else:
            all_artists = _sqlite_all_artists()
        for adata in all_artists:
            try:
                if adata.get("subscription_id") == sub_id:
                    if etype == "customer.subscription.deleted" or status == "canceled":
                        adata["subscription_status"] = "canceled"
                        adata["tier"] = "Gold"
                    else:
                        adata["subscription_status"] = status
                    _save_artist_file(adata["artist_id"], adata)
                    print(f"[STRIPE] sub {sub_id} → {status}")
                    break
            except Exception:
                pass

    return {"received": True}

@app.get("/api/billing/history")
async def get_billing_history(artist_id: str):
    try:
        _, data = _load_artist_file(artist_id)
        return {"history": data.get("billing_history", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── D-ID talking avatar ────────────────────────────────────────────────────────
import uuid as _uuid_mod
import numpy as _np

D_ID_API_KEY   = os.environ.get("D_ID_API_KEY", "")
D_ID_AVAILABLE = bool(D_ID_API_KEY)
TEMP_AUDIO_DIR = Path(os.environ.get("TEMP_AUDIO_DIR", _BASE / "static/temp_audio"))
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Cache: agent_id → D-ID image URL (uploaded once, reused)
_did_image_cache: dict = {}

def _did_auth() -> str:
    """D-ID Basic auth header value: base64(api_key:)"""
    return "Basic " + base64.b64encode(f"{D_ID_API_KEY}:".encode()).decode()

async def _ensure_did_image(agent_id: str) -> str:
    """Upload agent photo to D-ID once; return their CDN URL."""
    if agent_id in _did_image_cache:
        return _did_image_cache[agent_id]

    img_path = _BASE / "static" / "agents" / f"{agent_id}.jpg"
    if not img_path.exists():
        # Agent has no photo — use APP_BASE_URL served image (may not be public)
        url = f"{APP_BASE_URL}/static/agents/{agent_id}.jpg"
        _did_image_cache[agent_id] = url
        return url

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.d-id.com/images",
                headers={"Authorization": _did_auth()},
                files={"image": (f"{agent_id}.jpg", img_path.read_bytes(), "image/jpeg")},
            )
        if resp.status_code in (200, 201):
            url = resp.json().get("url", "")
            _did_image_cache[agent_id] = url
            print(f"[D-ID] uploaded image for {agent_id}: {url}")
            return url
    except Exception as e:
        print(f"[D-ID] image upload failed for {agent_id}: {e}")

    # Fallback: direct URL (works only if APP_BASE_URL is publicly reachable)
    url = f"{APP_BASE_URL}/static/agents/{agent_id}.jpg"
    _did_image_cache[agent_id] = url
    return url

def _concat_wav_chunks(chunks: list) -> bytes:
    """Concatenate list of base64-encoded WAV chunks into a single WAV."""
    import soundfile as sf
    all_samples = []
    sample_rate = 24000  # Kokoro default
    for b64_chunk in chunks:
        raw = base64.b64decode(b64_chunk)
        buf = io.BytesIO(raw)
        try:
            samples, sr = sf.read(buf)
            sample_rate = sr
            if samples.ndim > 1:
                samples = samples.mean(axis=1)  # stereo → mono
            all_samples.append(samples.astype(_np.float32))
        except Exception:
            pass
    if not all_samples:
        return b""
    combined = _np.concatenate(all_samples)
    out = io.BytesIO()
    sf.write(out, combined, sample_rate, format="WAV")
    return out.getvalue()

class AvatarTalkRequest(BaseModel):
    agent_id: str
    audio_chunks: list  # list of base64 WAV strings

@app.post("/api/avatar/talk")
async def avatar_talk(payload: AvatarTalkRequest):
    if not D_ID_AVAILABLE:
        raise HTTPException(status_code=503, detail="D-ID not configured — set D_ID_API_KEY")
    if not payload.audio_chunks:
        raise HTTPException(status_code=400, detail="No audio chunks provided")

    # Concatenate WAV chunks and save to temp file
    loop = asyncio.get_event_loop()
    audio_bytes = await loop.run_in_executor(None, _concat_wav_chunks, payload.audio_chunks)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Could not decode audio chunks")

    audio_id   = str(_uuid_mod.uuid4())[:12]
    audio_path = TEMP_AUDIO_DIR / f"{audio_id}.wav"
    audio_path.write_bytes(audio_bytes)
    audio_url  = f"{APP_BASE_URL}/static/temp_audio/{audio_id}.wav"

    # Ensure agent image is uploaded to D-ID
    source_url = await _ensure_did_image(payload.agent_id)

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            # Create talk
            create_resp = await client.post(
                "https://api.d-id.com/talks",
                headers={"Authorization": _did_auth(), "Content-Type": "application/json"},
                json={
                    "source_url": source_url,
                    "script": {
                        "type": "audio",
                        "audio_url": audio_url,
                    },
                    "config": {
                        "fluent": True,
                        "pad_audio": 0.0,
                        "stitch": True,
                    },
                },
            )
            if create_resp.status_code not in (200, 201):
                raise HTTPException(
                    status_code=502,
                    detail=f"D-ID create error {create_resp.status_code}: {create_resp.text[:300]}",
                )
            talk_id = create_resp.json().get("id", "")
            print(f"[D-ID] talk {talk_id} created for agent={payload.agent_id}")

            # Poll until done (max 60 s)
            for attempt in range(60):
                await asyncio.sleep(1)
                poll = await client.get(
                    f"https://api.d-id.com/talks/{talk_id}",
                    headers={"Authorization": _did_auth()},
                )
                data   = poll.json()
                status = data.get("status", "")
                if status == "done":
                    video_url = data.get("result_url", "")
                    print(f"[D-ID] talk {talk_id} ready in {attempt+1}s → {video_url}")
                    try:
                        audio_path.unlink()
                    except Exception:
                        pass
                    return {"video_url": video_url, "talk_id": talk_id}
                elif status in ("error", "rejected"):
                    raise HTTPException(
                        status_code=502,
                        detail=f"D-ID failed: {data.get('error', {}).get('description', status)}",
                    )

            raise HTTPException(status_code=504, detail="D-ID timeout — talk not ready in 60s")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"D-ID error: {e}")
    finally:
        # Clean up temp audio on any error path
        try:
            if audio_path.exists():
                audio_path.unlink()
        except Exception:
            pass

@app.get("/api/avatar/status")
async def avatar_status():
    """Check if D-ID avatar feature is available."""
    return {"available": D_ID_AVAILABLE}


# ── A&R Deep Assessment ────────────────────────────────────────────────────────

class ArScoutArtistInput(BaseModel):
    """Artist-level fields for the assessment. Name is taken from release/track
    metadata, NOT from the Playmaker account profile, to prevent account-name
    vs. credited-artist mismatches."""
    name:             str
    genre:            str
    stage:            str   = "emerging"   # emerging|developing|established|superstar
    territory:        str   = "unknown"
    monthly_listeners: Optional[int]   = None
    save_rate:        Optional[float]  = None  # 0.0–1.0
    release_count:    int   = 0
    manager:          Optional[str]    = None
    label:            Optional[str]    = None

class ArScoutTrackInput(BaseModel):
    title:            str
    bpm:              Optional[float]  = None
    duration_sec:     Optional[float]  = None
    lufs:             Optional[float]  = None
    intro_length_sec: Optional[float]  = None
    genre:            Optional[str]    = None
    features:         list[str]        = []
    release_date:     Optional[str]    = None  # YYYY-MM-DD if already released

class ArScoutAssessRequest(BaseModel):
    artist_id:       str         = ""   # Playmaker account id (for context; identity from artist field)
    artist:          ArScoutArtistInput
    track:           ArScoutTrackInput
    evaluation_stage: str        = "watching"  # watching|approach|due_diligence|internal_pitch
    additional_notes: str        = ""

_AR_SCOUT_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist": None,   # filled at runtime
    "track": None,    # filled at runtime
    "evaluation_stage": None,
    "assessment": {
        "pillars": {
            "music_quality":        {"grade": "B+", "numeric": 8.0, "confidence": "PARTIAL",
                                     "evaluable": ["emotional_impact (JUDGED)", "hook_speed (JUDGED)", "vocal_performance (JUDGED)"],
                                     "not_evaluable": ["production_quality — no audio analysis; confidence capped at PARTIAL",
                                                       "dynamic_progression — no audio analysis",
                                                       "chorus_lift — no audio analysis"]},
            "artist_identity":      {"grade": "B",  "numeric": 7.0, "confidence": "PARTIAL",
                                     "evaluable": ["authenticity (JUDGED)", "uniqueness (JUDGED)", "storytelling (JUDGED)"],
                                     "not_evaluable": ["interview_personality — no live/interview material",
                                                       "fan_connection — no platform analytics provided"]},
            "audience_market":      {"grade": "C+", "numeric": 6.0, "confidence": "LOW",
                                     "evaluable": ["release_count (SOURCED)"],
                                     "not_evaluable": ["save_rate — not provided",
                                                       "monthly_listener_growth — no trajectory data",
                                                       "repeat_listening — no analytics provided"]},
            "execution_team":       {"grade": "C",  "numeric": 5.0, "confidence": "PARTIAL",
                                     "evaluable": ["release_consistency (SOURCED)"],
                                     "not_evaluable": ["manager_quality — manager not identified",
                                                       "responsiveness — NOT EVALUABLE without direct contact",
                                                       "financial_discipline — NOT EVALUABLE without direct relationship"]},
            "commercial_opportunity":{"grade": "B-", "numeric": 6.5, "confidence": "PARTIAL",
                                      "evaluable": ["playlist (JUDGED)", "sync (JUDGED)"],
                                      "not_evaluable": ["radio — format fit requires measured audio data",
                                                        "international — territory data not provided"]}
        },
        "composite": {
            "value": 6.7,
            "formula": "(8.0×0.30) + (7.0×0.25) + (6.0×0.20) + (5.0×0.15) + (6.5×0.10)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked evaluations in feedback/outcomes/"
        },
        "hard_gates": {
            "gate1_production_floor": "CLEAR — production not evaluable without audio, but no hard-fail signal present",
            "gate2_identity_floor":   "CLEAR — identity signals present and evaluable",
            "gate3_no_commercial_lane":"CLEAR — at least one commercial pathway identifiable",
            "gate4_execution_floor":  "CLEAR — execution signals present; team gaps noted"
        },
        "verdict": "DEVELOP",
        "verdict_rationale": "Composite 6.7 falls in 6.5–7.9 range. Trajectory data is NOT EVALUABLE (no analytics provided), defaulting to DEVELOP split. Execution & Team grade C — team gaps require active development investment before pipeline advancement.",
        "trajectory": {
            "monthly_listener_growth": "NOT EVALUABLE — no analytics provided",
            "save_rate_trend":         "NOT EVALUABLE — no release history provided",
            "repeat_listening":        "NOT EVALUABLE",
            "release_consistency":     "Neutral — release count noted but cadence not evaluable from input",
            "trajectory_grade":        "Weak (data absent — defaults to DEVELOP split)"
        },
        "unfair_advantage": {
            "identified": [],
            "assessment": "None identified from available materials. Direct working-relationship evidence would be required to assess elite work ethic or exceptional live show."
        },
        "career_ceiling": {
            "tier": "National",
            "confidence": "Low",
            "reason": "Genre and stage suggest national ceiling is achievable; insufficient trajectory data to support International claim. Confidence LOW — capped by NOT EVALUABLE audience signals.",
            "catalyst_for_next_tier": "Documented positive save-rate trend across 2+ releases + at least one editorial playlist add would move confidence to Medium for International ceiling."
        },
        "risk_assessment": {
            "execution":       {"level": "Medium", "reason": "No manager identified; release cadence history not evaluable from input."},
            "financial":       {"level": "Medium", "reason": "Investment case realistic at National ceiling; recoupment plausible with consistent release cadence."},
            "reputation":      {"level": "Low",    "reason": "No known controversies or brand risks identified from available materials."},
            "team":            {"level": "High",   "reason": "Manager not identified; team qualification for development phase NOT EVALUABLE."},
            "legal":           {"level": "Medium", "reason": "IP ownership and deal encumbrances not confirmed from available materials."},
            "burnout":         {"level": "Low",    "reason": "No evidence of creative or personal overextension from available materials."},
            "ai_displacement": {"level": "Medium", "reason": "Genre-specific differentiation not yet fully established; identity moat requires further development."},
            "trend_dependency":{"level": "Medium", "reason": "Genre trajectory not assessed — insufficient market data in input."}
        },
        "five_year_test": {
            "question": "If this artist debuts today, could they still matter five years from now after trends change, algorithms change, and AI-generated music becomes ubiquitous?",
            "answer":   "CONDITIONAL — the identity signals present are promising but insufficiently documented. If the artist establishes an ownable sonic and narrative identity before the first major release (identity clarity test from artist-development.md), and executes a consistent waterfall release cadence, the foundation for a 5-year career is buildable. Specific condition: artist must be able to articulate their identity in one sentence without genre clichés before proceeding to Phase 2. Until that condition clears, the five-year case rests on potential, not demonstrated differentiation."
        },
        "owner_input_pending": "Identity and Execution assessment based on available materials only — direct relationship signals (responsiveness, financial discipline, professionalism) NOT EVALUABLE at this stage.",
        "remediation_priorities": [
            "Identify and engage a manager with demonstrated development-to-breakthrough track record — Hard Gate 4 risk zone until team is in place.",
            "Provide platform analytics (Spotify for Artists / Apple Music) for save-rate, monthly listener trajectory, and repeat-listening data — three pillars currently at LOW or PARTIAL confidence.",
            "Run the identity clarity test: can the artist articulate who they are in one sentence without genre clichés? If not, identity development precedes release.",
        ]
    },
    "model": "claude-sonnet-4-6",
    "mock_note": "AR_SCOUT_MOCK_MODE=true — this is a canned assessment. Set AR_SCOUT_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}

def _render_ar_scorecard_html(assessment: dict, artist: dict, track: dict) -> str:
    """Render an A&R assessment dict as a standalone HTML scorecard page."""
    pillar_color = {
        "A+": "#16a34a", "A": "#22c55e", "A-": "#4ade80",
        "B+": "#84cc16", "B": "#a3e635", "B-": "#d9f99d",
        "C+": "#facc15", "C": "#fbbf24", "C-": "#f59e0b",
        "D+": "#f97316", "D": "#ef4444", "D-": "#dc2626",
        "F":  "#991b1b",
    }
    verdict_color = {
        "PASS": "#991b1b", "WATCH": "#b45309", "DEVELOP": "#1d4ed8",
        "PURSUE": "#7c3aed", "GREENLIGHT": "#15803d", "SIGN IMMEDIATELY": "#065f46",
    }

    pillars      = assessment.get("pillars", {})
    composite    = assessment.get("composite", {})
    verdict      = assessment.get("verdict", "UNKNOWN")
    ceiling      = assessment.get("career_ceiling", {})
    risks        = assessment.get("risk_assessment", {})
    fyt          = assessment.get("five_year_test", {})
    trajectory   = assessment.get("trajectory", {})
    unfair_adv   = assessment.get("unfair_advantage", {})
    remediation  = assessment.get("remediation_priorities", [])
    hard_gates   = assessment.get("hard_gates", {})

    pillar_rows = ""
    pillar_names = {
        "music_quality": "Music Quality (0.30)",
        "artist_identity": "Artist Identity & Brand (0.25)",
        "audience_market": "Audience & Market (0.20)",
        "execution_team": "Execution & Team (0.15)",
        "commercial_opportunity": "Commercial Opportunity (0.10)",
    }
    for key, label in pillar_names.items():
        p = pillars.get(key, {})
        grade = p.get("grade", "?")
        color = pillar_color.get(grade, "#6b7280")
        conf  = p.get("confidence", "?")
        not_ev = "; ".join(p.get("not_evaluable", [])[:2]) or "—"
        pillar_rows += f"""
        <tr>
          <td style="padding:8px 12px;font-weight:600;">{label}</td>
          <td style="padding:8px 12px;text-align:center;">
            <span style="background:{color};color:#fff;padding:3px 10px;border-radius:4px;font-weight:700;">{grade}</span>
          </td>
          <td style="padding:8px 12px;font-size:0.85em;color:#6b7280;">{conf}</td>
          <td style="padding:8px 12px;font-size:0.82em;color:#9ca3af;">{not_ev}</td>
        </tr>"""

    gate_rows = ""
    gate_labels = {
        "gate1_production_floor": "Gate 1 — Production Floor",
        "gate2_identity_floor":   "Gate 2 — Identity Floor",
        "gate3_no_commercial_lane":"Gate 3 — No Commercial Lane",
        "gate4_execution_floor":  "Gate 4 — Execution & Team Floor",
    }
    for k, label in gate_labels.items():
        v = hard_gates.get(k, "NOT ASSESSED")
        triggered = "TRIGGERED" in v.upper()
        color = "#991b1b" if triggered else "#15803d"
        badge = "TRIGGERED" if triggered else "CLEAR"
        gate_rows += f"""
        <tr>
          <td style="padding:6px 12px;font-size:0.9em;">{label}</td>
          <td style="padding:6px 12px;">
            <span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:0.8em;font-weight:700;">{badge}</span>
          </td>
          <td style="padding:6px 12px;font-size:0.82em;color:#6b7280;">{v[:80]}{'…' if len(v)>80 else ''}</td>
        </tr>"""

    risk_rows = ""
    risk_level_color = {"Low": "#15803d", "Medium": "#b45309", "High": "#991b1b"}
    for cat, data in risks.items():
        level  = data.get("level", "?")
        reason = data.get("reason", "")
        color  = risk_level_color.get(level, "#6b7280")
        risk_rows += f"""
        <tr>
          <td style="padding:6px 12px;font-size:0.9em;text-transform:capitalize;">{cat.replace('_',' ')}</td>
          <td style="padding:6px 12px;">
            <span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:0.8em;font-weight:700;">{level}</span>
          </td>
          <td style="padding:6px 12px;font-size:0.82em;color:#6b7280;">{reason}</td>
        </tr>"""

    remediation_items = "".join(
        f'<li style="margin-bottom:8px;">{item}</li>'
        for item in remediation
    )

    v_color = verdict_color.get(verdict, "#374151")
    comp_val = composite.get("value", "?")
    comp_label = composite.get("label", "")

    unfair_list = unfair_adv.get("identified", [])
    unfair_note = unfair_adv.get("assessment", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PLMKR A&R Assessment — {artist.get('name','?')}</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px;}}
  .card{{background:#1e293b;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #334155;}}
  h1{{font-size:1.6em;margin:0 0 4px;}}
  h2{{font-size:1.1em;color:#94a3b8;margin:0 0 16px;font-weight:500;}}
  h3{{font-size:1em;color:#64748b;margin:0 0 12px;text-transform:uppercase;letter-spacing:.05em;}}
  table{{width:100%;border-collapse:collapse;}}
  tr:nth-child(even){{background:rgba(255,255,255,.03);}}
  .verdict{{font-size:2em;font-weight:800;padding:8px 20px;border-radius:8px;display:inline-block;color:#fff;}}
  .comp{{font-size:1.4em;font-weight:700;}}
  .provisional{{font-size:0.75em;color:#94a3b8;font-weight:400;}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:0.8em;font-weight:700;}}
  ul{{margin:0;padding-left:20px;color:#cbd5e1;}}
  p{{color:#cbd5e1;line-height:1.6;margin:0;}}
  .meta{{color:#64748b;font-size:0.85em;}}
</style>
</head>
<body>
<div style="max-width:900px;margin:0 auto;">

<div class="card">
  <h1>PLMKR A&R Assessment</h1>
  <h2>Signing Evaluation Memo — {artist.get('name','?')}</h2>
  <div class="meta">Track: "{track.get('title','?')}" &nbsp;|&nbsp; Stage: {artist.get('stage','?')} &nbsp;|&nbsp; Genre: {artist.get('genre','?')} &nbsp;|&nbsp; Territory: {artist.get('territory','?')}</div>
</div>

<div class="card" style="display:flex;gap:32px;align-items:center;">
  <div>
    <h3>Verdict</h3>
    <div class="verdict" style="background:{v_color};">{verdict}</div>
  </div>
  <div>
    <h3>Provisional Composite</h3>
    <div class="comp">{comp_val}</div>
    <div class="provisional">{comp_label} — unlock condition: ≥30 outcome-checked evaluations in feedback/outcomes/</div>
  </div>
  <div>
    <h3>Career Ceiling</h3>
    <div style="font-size:1.3em;font-weight:700;">{ceiling.get('tier','?')}</div>
    <div class="meta">Confidence: {ceiling.get('confidence','?')}</div>
  </div>
</div>

<div class="card">
  <h3>Pillar Scores (Five-Pillar Model)</h3>
  <table>
    <thead><tr style="color:#64748b;font-size:0.8em;text-transform:uppercase;">
      <th style="text-align:left;padding:6px 12px;">Pillar</th>
      <th style="padding:6px 12px;">Grade</th>
      <th style="text-align:left;padding:6px 12px;">Confidence</th>
      <th style="text-align:left;padding:6px 12px;">Key NOT EVALUABLE items</th>
    </tr></thead>
    <tbody>{pillar_rows}</tbody>
  </table>
</div>

<div class="card">
  <h3>Hard Gates</h3>
  <table>
    <thead><tr style="color:#64748b;font-size:0.8em;text-transform:uppercase;">
      <th style="text-align:left;padding:6px 12px;">Gate</th>
      <th style="padding:6px 12px;">Status</th>
      <th style="text-align:left;padding:6px 12px;">Note</th>
    </tr></thead>
    <tbody>{gate_rows}</tbody>
  </table>
</div>

<div class="card">
  <h3>Trajectory Assessment</h3>
  <table>
    {''.join(f'<tr><td style="padding:6px 12px;color:#94a3b8;font-size:0.9em;">{k.replace("_"," ").title()}</td><td style="padding:6px 12px;font-size:0.9em;">{v}</td></tr>' for k,v in trajectory.items())}
  </table>
</div>

<div class="card">
  <h3>Unfair Advantage Assessment</h3>
  <p>{unfair_note}</p>
  {'<ul>' + ''.join(f'<li>{a}</li>' for a in unfair_list) + '</ul>' if unfair_list else ''}
</div>

<div class="card">
  <h3>Risk Assessment</h3>
  <table>
    <thead><tr style="color:#64748b;font-size:0.8em;text-transform:uppercase;">
      <th style="text-align:left;padding:6px 12px;">Category</th>
      <th style="padding:6px 12px;">Level</th>
      <th style="text-align:left;padding:6px 12px;">Reason</th>
    </tr></thead>
    <tbody>{risk_rows}</tbody>
  </table>
</div>

<div class="card">
  <h3>Five-Year Test</h3>
  <p style="font-style:italic;color:#94a3b8;margin-bottom:12px;">{fyt.get('question','')}</p>
  <p>{fyt.get('answer','')}</p>
</div>

<div class="card">
  <h3>Career Ceiling Rationale</h3>
  <p><strong style="color:#e2e8f0;">{ceiling.get('tier','?')}</strong> — {ceiling.get('reason','')}</p>
  {f'<p style="margin-top:10px;color:#64748b;font-size:0.88em;"><strong>Catalyst for next tier:</strong> {ceiling.get("catalyst_for_next_tier","—")}</p>' if ceiling.get("catalyst_for_next_tier") else ''}
</div>

<div class="card">
  <h3>Remediation Priorities</h3>
  <ol>{remediation_items}</ol>
</div>

<div class="card" style="text-align:center;color:#475569;font-size:0.8em;">
  PLMKR A&R Assessment &nbsp;|&nbsp; Rubric v1.0 — Five-Pillar Model &nbsp;|&nbsp; Composite: PROVISIONAL (unlock ≥30 evaluated outcomes)
</div>

</div>
</body>
</html>"""


@app.get("/api/agents/ar-scout/assess/demo", tags=["ar-scout"])
async def ar_scout_assess_demo():
    """
    Render a mocked A&R scored assessment as a standalone HTML scorecard.
    Demonstrates the pilot end-to-end without any live API calls.
    """
    sample_artist = {
        "name": "Jordan Voss", "genre": "R&B / Soul", "stage": "emerging",
        "territory": "Canada", "monthly_listeners": 28000, "save_rate": 0.062,
        "release_count": 4, "manager": None, "label": None,
    }
    sample_track = {
        "title": "Still Waters", "bpm": 88.0, "duration_sec": 213.0,
        "lufs": None, "intro_length_sec": 14.0,
        "genre": None, "features": [], "release_date": None,
    }
    import main as _m
    mock_result = dict(_m._AR_SCOUT_MOCK_ASSESSMENT)
    mock_result["artist"] = sample_artist
    mock_result["track"]  = sample_track

    html = _render_ar_scorecard_html(mock_result["assessment"], sample_artist, sample_track)
    return HTMLResponse(content=html)


@app.post("/api/agents/ar-scout/assess", tags=["ar-scout"])
async def ar_scout_assess(req: ArScoutAssessRequest):
    """
    Deep A&R assessment for a PLMKR artist + track.

    Artist identity is bound from the request payload (artist.name from release/
    track metadata), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When AR_SCOUT_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set AR_SCOUT_MOCK_MODE=false with a
    valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if AR_SCOUT_MOCK_MODE:
        result = dict(_AR_SCOUT_MOCK_ASSESSMENT)
        result["artist"] = req.artist.model_dump()
        result["track"]  = req.track.model_dump()
        result["evaluation_stage"] = req.evaluation_stage
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set AR_SCOUT_MOCK_MODE=true to use mock mode.")

    system_prompt = build_ar_scout_system_prompt(skills_dir=SKILLS_DIR)

    # Build the structured user prompt with every field explicitly labeled
    artist = req.artist
    track  = req.track

    user_prompt = f"""You are performing a PLMKR A&R deep assessment. Use the scoring rubric, song evaluation framework, and output templates from your knowledge base to produce a complete Signing Evaluation Memo.

EVALUATION STAGE: {req.evaluation_stage}

ARTIST PROFILE (from release/track metadata — use this for artist identity, not any account profile name):
- Credited artist name: {artist.name}
- Primary genre: {artist.genre}
- Career stage: {artist.stage}
- Primary territory: {artist.territory}
- Monthly listeners: {artist.monthly_listeners if artist.monthly_listeners is not None else 'NOT PROVIDED — mark as NOT EVALUABLE'}
- Save rate (most recent release): {f'{artist.save_rate:.1%}' if artist.save_rate is not None else 'NOT PROVIDED — mark as NOT EVALUABLE'}
- Total release count: {artist.release_count}
- Manager: {artist.manager or 'NOT IDENTIFIED — flag as Hard Gate 4 risk'}
- Label: {artist.label or 'Independent / not identified'}

TRACK DETAILS:
- Track title: {track.title}
- BPM: {track.bpm if track.bpm is not None else 'NOT PROVIDED — mark Hook Speed and DSP Friendliness as NOT EVALUABLE from measured data'}
- Duration: {f'{track.duration_sec:.0f}s ({track.duration_sec/60:.1f} min)' if track.duration_sec is not None else 'NOT PROVIDED'}
- Integrated LUFS: {track.lufs if track.lufs is not None else 'NOT PROVIDED — mark Production Quality as NOT EVALUABLE from measured data; confidence cap applies'}
- Intro length to hook/vocal: {f'{track.intro_length_sec:.0f}s' if track.intro_length_sec is not None else 'NOT PROVIDED — skip risk assessment requires this; mark as NOT EVALUABLE'}
- Track genre (if different from artist genre): {track.genre or 'same as artist genre'}
- Features / collaborators: {', '.join(track.features) if track.features else 'none'}
- Release date: {track.release_date or 'unreleased'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST PROFILE above (credited artist name), not any other name or account reference.
2. For every sub-signal, explicitly state whether it is MEASURED, SOURCED, or JUDGED, and whether it is EVALUABLE or NOT EVALUABLE based on the data provided above.
3. If a measured audio field (LUFS, BPM, intro length) is NOT PROVIDED, mark it NOT EVALUABLE — do not estimate or infer it.
4. Apply the Anti-Fake-Precision mechanics from the scoring rubric: no probability percentages, no fabricated comparables, no invented unfair advantages.
5. Do not use any retention/threshold language as sourced data claims — frame all benchmarks as industry convention (Tier B estimates), never as verified data.
6. Produce the complete 8-element Signing Evaluation Memo format from the output template.
7. End with a JSON-compatible structured scorecard block labelled STRUCTURED_SCORECARD_JSON containing: verdict, composite_value, pillar_grades (dict), career_ceiling, and top_3_remediation_priorities (list).
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"A&R assessment failed: {str(e)}")

    return {
        "status":           "ok",
        "mock":             False,
        "artist":           req.artist.model_dump(),
        "track":            req.track.model_dump(),
        "evaluation_stage": req.evaluation_stage,
        "assessment_text":  assessment_text,
        "model":            MODEL_SONNET,
    }


# ── GRID-PROPHET — Marketing Assessment ───────────────────────────────────────

class GridProphetArtistInput(BaseModel):
    """Artist-level fields for the marketing assessment. Name is taken from
    release/track metadata, NOT from the Playmaker account profile."""
    name:             str
    genre:            str
    stage:            str   = "emerging"   # emerging|developing|established|superstar
    territory:        str   = "unknown"
    monthly_listeners: Optional[int]   = None
    social_following:  Optional[int]   = None   # total cross-platform
    save_rate:         Optional[float] = None   # 0.0–1.0 on most recent release
    release_count:     int   = 0
    has_email_list:    bool  = False
    email_list_size:   Optional[int]   = None
    has_merch:         bool  = False
    prior_editorial_placements: int = 0

class GridProphetCampaignInput(BaseModel):
    release_title:       str
    release_date:        Optional[str]   = None   # YYYY-MM-DD or None if unreleased
    campaign_budget_usd: Optional[float] = None
    campaign_window_weeks: int = 12
    primary_platforms:   list[str] = []   # e.g. ["tiktok", "instagram", "spotify"]
    has_tour_dates:      bool = False
    tour_territory:      Optional[str]   = None
    is_catalog_campaign: bool = False

class GridProphetAssessRequest(BaseModel):
    artist_id:        str   = ""
    artist:           GridProphetArtistInput
    campaign:         GridProphetCampaignInput
    additional_notes: str   = ""

_GRID_PROPHET_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist": None,    # filled at runtime
    "campaign": None,  # filled at runtime
    "assessment": {
        "dimensions": {
            "virality": {
                "score": 6.0, "weight": 0.15, "confidence": "PARTIAL",
                "evidence": "Genre has documented TikTok sound track record at this scale. Hook structure is excerpt-friendly per track profile.",
                "not_evaluable": ["pre-release organic spread — no social listening data provided",
                                  "UGC velocity — no comparable track history provided"]
            },
            "ugc_potential": {
                "score": 5.0, "weight": 0.12, "confidence": "PARTIAL",
                "evidence": "Genre supports participatory format (singalong, lip-sync). Audio excerpt-worthy based on genre profile.",
                "not_evaluable": ["prior UGC on artist catalog — no analytics provided",
                                  "challenge/movement vector — no release concept details provided"]
            },
            "platform_fit": {
                "score": 5.5, "weight": 0.18, "confidence": "LOW",
                "evidence": "Platform list provided; genre indicates plausible fit on primary platforms.",
                "not_evaluable": ["posting cadence — no social analytics provided",
                                  "engagement rate vs. cohort benchmark — no platform analytics provided",
                                  "algorithm growth state — cannot assess without recent post performance data"]
            },
            "editorial_readiness": {
                "score": 4.0, "weight": 0.13, "confidence": "PARTIAL",
                "evidence": "Release date provided; pitch window can be assessed once EPK status confirmed.",
                "not_evaluable": ["metadata completeness — distributor QC not confirmed",
                                  "EPK status — bio, press photo, embed player not confirmed",
                                  "editorial contact — not provided"]
            },
            "touring_synergy": {
                "score": 3.0, "weight": 0.03, "confidence": "LOW",
                "evidence": "No tour dates confirmed in campaign input.",
                "not_evaluable": ["live activity within campaign window — not provided"]
            },
            "merch_d2c": {
                "score": 3.0, "weight": 0.10, "confidence": "PARTIAL",
                "evidence": "Merch status and email list provided at binary level; size and conversion history not evaluable.",
                "not_evaluable": ["email list open rate — not provided",
                                  "D2C purchase history — not provided",
                                  "physical format plans — not provided"]
            },
            "brand_partnership": {
                "score": 4.0, "weight": 0.07, "confidence": "LOW",
                "evidence": "Monthly listener range indicates brand interest threshold may not yet be met at sub-100K scale.",
                "not_evaluable": ["brand-safety record — no public controversy check data provided",
                                  "prior brand work — not provided",
                                  "category openness — not provided"]
            },
            "fan_ltv": {
                "score": 4.0, "weight": 0.22, "confidence": "PARTIAL",
                "evidence": "Release count and email list presence are structural LTV signals. Save rate provided as proxy for depth of listen.",
                "not_evaluable": ["ticket conversion history — no live event data provided",
                                  "catalog re-listen behavior — no streaming analytics provided",
                                  "community platform (Discord/Patreon) — not provided"]
            }
        },
        "composite": {
            "value": 4.6,
            "formula": "(6.0×0.15) + (5.0×0.12) + (5.5×0.18) + (4.0×0.13) + (3.0×0.03) + (3.0×0.10) + (4.0×0.07) + (4.0×0.22)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked campaign evaluations in feedback/outcomes/"
        },
        "band": "Amber",
        "band_meaning": "Limited campaign — address gap dimensions before full spend; partial rollout",
        "hard_gates": {
            "editorial_gate":    "CONDITIONAL — Editorial Readiness scored 4. Metadata and EPK must be confirmed clean before any editorial pitch submission. Score of 1 would block pitch.",
            "paid_spend_gate":   "CLEAR — Platform Fit scored 5.5 (above gate threshold of ≤2). Paid spend can proceed with caution; recommend small-scale test first.",
            "brand_pitch_gate":  "BLOCKED — Brand Partnership Potential scored 4 (≤2 threshold not triggered at 4; gate not active). However, audience size NOT EVALUABLE — confirm monthly listeners ≥50K before pursuing brand outreach."
        },
        "campaign_priorities": [
            "Confirm EPK completeness (bio, press photo, metadata) — this is a hard gate for editorial and blocks Spotify pitch if any field is missing.",
            "Obtain platform analytics (Spotify for Artists, TikTok/Instagram analytics) — Platform Fit is the highest-weighted gap dimension; cannot score confidently without posting cadence and engagement rate data.",
            "Build or grow email list before launch — Fan LTV potential is the highest-weight dimension (0.22); email list is the single highest-LTV fan acquisition channel available to this artist at this stage."
        ],
        "channel_mix_recommendation": {
            "organic_social": {
                "allocation": "50%", "rationale": "Primary platform algorithm building. TikTok/Reels cadence must be established before paid amplification.",
                "measurement": "Organic engagement rate, completion rate, follower growth WoW"
            },
            "editorial_pitch": {
                "allocation": "0% budget (relationship-earned)", "rationale": "Highest-value non-paid channel. Priority: Spotify editorial 7+ days pre-release.",
                "measurement": "Editorial add within 72h of release"
            },
            "email_sms": {
                "allocation": "10%", "rationale": "Highest LTV-per-dollar channel for artists with existing list. Pre-save push in Phase 2.",
                "measurement": "Pre-save click rate, email open rate, D2C conversion rate"
            },
            "paid_social": {
                "allocation": "40%", "rationale": "Retargeting warm audiences (video viewers ≥50%, profile visitors, prior savers). Cold prospecting only at 10–15% of paid budget until CPA is proven.",
                "measurement": "Cost-per-pre-save, cost-per-follower, warm vs. cold audience CPM ratio"
            }
        },
        "confidence_cap": "Composite confidence capped at LOW: Platform Fit and Fan LTV scored PARTIAL or LOW — platform analytics and conversion history not provided. Assessment cannot be confidently scored above Amber band without these inputs.",
        "next_best_action": "Provide Spotify for Artists analytics (monthly listener count, save rate, completion rate) and social posting cadence data — these two inputs would move Platform Fit and Fan LTV from PARTIAL/LOW to PARTIAL/MEDIUM and may shift the composite band from Amber to Yellow."
    },
    "model": "claude-sonnet-4-6",
    "mock_note": "GRID_PROPHET_MOCK_MODE=true — this is a canned assessment. Set GRID_PROPHET_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/grid-prophet/assess", tags=["grid-prophet"])
async def grid_prophet_assess(req: GridProphetAssessRequest):
    """
    Marketing readiness assessment for a PLMKR artist + campaign.

    Artist identity is bound from the request payload (artist.name from release/
    track metadata), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When GRID_PROPHET_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set GRID_PROPHET_MOCK_MODE=false with a
    valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if GRID_PROPHET_MOCK_MODE:
        result = dict(_GRID_PROPHET_MOCK_ASSESSMENT)
        result["artist"]   = req.artist.model_dump()
        result["campaign"] = req.campaign.model_dump()
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set GRID_PROPHET_MOCK_MODE=true to use mock mode.")

    system_prompt = build_grid_prophet_system_prompt(skills_dir=SKILLS_DIR)

    artist   = req.artist
    campaign = req.campaign

    user_prompt = f"""You are performing a PLMKR marketing readiness assessment. Use the scoring rubric, campaign architecture, channel economics, and output templates from your knowledge base to produce a complete Campaign Plan assessment.

ARTIST PROFILE (from release/track metadata — use this for artist identity, not any account profile name):
- Credited artist name: {artist.name}
- Primary genre: {artist.genre}
- Career stage: {artist.stage}
- Primary territory: {artist.territory}
- Monthly listeners: {artist.monthly_listeners if artist.monthly_listeners is not None else 'NOT PROVIDED — mark as NOT EVALUABLE'}
- Social following (cross-platform): {artist.social_following if artist.social_following is not None else 'NOT PROVIDED'}
- Save rate (most recent release): {f'{artist.save_rate:.1%}' if artist.save_rate is not None else 'NOT PROVIDED — mark as NOT EVALUABLE'}
- Total release count: {artist.release_count}
- Email list: {'YES — size: ' + str(artist.email_list_size) if artist.has_email_list else 'NO — flag as LTV gap'}
- Merch available: {'YES' if artist.has_merch else 'NO'}
- Prior editorial placements: {artist.prior_editorial_placements}

CAMPAIGN DETAILS:
- Release title: {campaign.release_title}
- Release date: {campaign.release_date or 'unreleased / TBD'}
- Campaign budget: {f'${campaign.campaign_budget_usd:,.0f}' if campaign.campaign_budget_usd is not None else 'NOT PROVIDED'}
- Campaign window: {campaign.campaign_window_weeks} weeks
- Primary platforms: {', '.join(campaign.primary_platforms) if campaign.primary_platforms else 'NOT PROVIDED'}
- Tour dates within campaign window: {'YES — territory: ' + (campaign.tour_territory or 'unspecified') if campaign.has_tour_dates else 'NO'}
- Catalog campaign (vs. new release): {'YES' if campaign.is_catalog_campaign else 'NO'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST PROFILE above (credited artist name), not any other name or account reference.
2. Score all 8 rubric dimensions. For each, explicitly state whether evidence is OBSERVED, TOLD, or INFERRED, and whether the dimension is EVALUABLE or NOT EVALUABLE from the data above.
3. If a required data field is NOT PROVIDED, mark it NOT EVALUABLE — do not estimate or infer it.
4. Apply the scoring rubric composite formula. Label the composite PROVISIONAL with the unlock condition.
5. State all hard gates (Editorial Gate, Paid Spend Gate, Brand Pitch Gate) — CLEAR or BLOCKED with reason.
6. Recommend a channel mix with stated mechanism and measurement method for each channel.
7. Name the top 3 campaign priorities and the single next best action (24–72h).
8. Do not use probability percentage language for any projection. Label all projections ESTIMATE with the comparable that produced them.
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=6000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Marketing assessment failed: {str(e)}")

    return {
        "status":        "ok",
        "mock":          False,
        "artist":        req.artist.model_dump(),
        "campaign":      req.campaign.model_dump(),
        "assessment_text": assessment_text,
        "model":         MODEL_SONNET,
    }


# ── BRAND-CONNECT — Brand Partnership Deal Quality Assessment ──────────────────

class BrandConnectArtistInput(BaseModel):
    """Artist-level fields for the brand partnership assessment. Name is taken
    from release/track metadata, NOT from the Playmaker account profile."""
    name:              str
    genre:             str
    stage:             str   = "emerging"   # emerging|developing|established|superstar
    territory:         str   = "unknown"
    tier:              str   = "GOLD"       # GOLD|PLATINUM|DIAMOND
    monthly_listeners: Optional[int]   = None
    social_following:  Optional[int]   = None   # total cross-platform
    engagement_rate:   Optional[float] = None   # 0.0–1.0

class BrandConnectDealInput(BaseModel):
    deal_type:              str   = "paid_social"  # product_gifting|paid_social|ambassador|tour_sponsorship|equity
    partner_category:       str   = "consumer_brand"
    exclusivity_category:   Optional[str]  = None
    term_months:            Optional[int]  = None
    has_kill_fee:           Optional[bool] = None
    upfront_payment_pct:    Optional[float] = None   # 0.0–1.0; fraction paid at signing
    diligence_status:       str   = "none"   # none|partial|full
    prior_artist_deals:     Optional[int]  = None   # brand's documented prior artist partnerships
    has_morality_clause:    Optional[bool] = None
    morality_clause_scoped: Optional[bool] = None   # True if specific triggers defined

class BrandConnectAssessRequest(BaseModel):
    artist_id:        str   = ""
    artist:           BrandConnectArtistInput
    deal:             BrandConnectDealInput
    additional_notes: str   = ""

_BRAND_CONNECT_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist": None,   # filled at runtime
    "deal":   None,   # filled at runtime
    "assessment": {
        "dimensions": {
            "strategic_value": {
                "score": 5.5, "weight": 0.18, "confidence": "PARTIAL",
                "evidence": "Deal type indicates audience access potential in artist's genre. Leverage-transfer test requires confirmation of brand's consumer demographic overlap with artist's listener base.",
                "not_evaluable": ["confirmed audience demographic overlap — brand consumer data not provided",
                                  "co-marketing spend commitment — not confirmed as contractually committed vs. aspirational"]
            },
            "economic_value": {
                "score": 5.0, "weight": 0.16, "confidence": "LOW",
                "evidence": "Deal type provided; specific consideration not provided. Payment schedule status unconfirmed.",
                "not_evaluable": ["total consideration amount — not provided",
                                  "production cost obligations — not assessed",
                                  "kill fee amount — not confirmed at this stage"]
            },
            "partner_quality": {
                "score": 3.0, "weight": 0.14, "confidence": "LOW",
                "evidence": "Diligence status: none. Prior artist deal count not confirmed. Proceeding without adequate credibility evidence — scored INFERRED at baseline.",
                "not_evaluable": ["brand payment track record — diligence not conducted",
                                  "creative approval process timeline — not assessed",
                                  "brand organizational alignment — not confirmed"]
            },
            "deal_structure": {
                "score": 4.0, "weight": 0.14, "confidence": "LOW",
                "evidence": "Term not confirmed. Category exclusivity scope not defined. Kill fee status not provided.",
                "not_evaluable": ["exclusivity category scope — not confirmed",
                                  "creative approval rounds and SLA — not assessed",
                                  "IP ownership of content created — not confirmed",
                                  "artist exit right — not confirmed"]
            },
            "risk_exposure": {
                "score": 4.0, "weight": 0.14, "confidence": "PARTIAL",
                "evidence": "Morality clause status not confirmed. No fatal exposure identified from available information, but morality clause assessment is incomplete.",
                "not_evaluable": ["morality clause trigger specificity — not assessed",
                                  "brand reputation controversy check — not conducted",
                                  "category exclusivity vs. alternative revenue impact — not assessed"]
            },
            "execution_feasibility": {
                "score": 5.0, "weight": 0.10, "confidence": "LOW",
                "evidence": "Deal type (paid social) indicates standard content delivery scope. Specific deliverable requirements and production timeline not confirmed.",
                "not_evaluable": ["production bandwidth assessment — not provided",
                                  "content calendar conflict with existing commitments — not assessed"]
            },
            "opportunity_cost": {
                "score": 3.0, "weight": 0.08, "confidence": "LOW",
                "evidence": "Category exclusivity scope not confirmed. Alternative brand partnerships in same category not identified or assessed. BATNA not established.",
                "not_evaluable": ["alternative brand opportunities in same category — not assessed",
                                  "exclusivity cost vs. best foreclosed alternative — not quantified"]
            },
            "reversibility": {
                "score": 4.0, "weight": 0.06, "confidence": "LOW",
                "evidence": "Kill fee and exit right status not confirmed. Term length not confirmed.",
                "not_evaluable": ["artist-exercisable exit right — not confirmed",
                                  "kill fee structure — not confirmed",
                                  "renewal terms — not confirmed"]
            }
        },
        "composite": {
            "value": 4.3,
            "formula": "(5.5×0.18) + (5.0×0.16) + (3.0×0.14) + (4.0×0.14) + (4.0×0.14) + (5.0×0.10) + (3.0×0.08) + (4.0×0.06)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked brand partnership evaluations in feedback/outcomes/"
        },
        "band": "Amber",
        "band_meaning": "Material gaps require resolution before committing — deal structure, partner diligence, and opportunity cost are all under-assessed at this stage",
        "hard_gates": {
            "partner_quality_gate": "CONDITIONAL — Partner Quality & Credibility scored 3 (INFERRED — diligence not conducted). Hard gate threshold is score 1 (disqualifying partner confirmed). Current score reflects absence of evidence, not negative evidence. Conduct partner diligence before commitment.",
            "risk_exposure_gate":   "CONDITIONAL — Risk & Downside Exposure scored 4. Hard gate threshold is score 1 (fatal, unmitigated exposure confirmed). Morality clause specificity must be confirmed before commitment. No fatal exposure identified from available information."
        },
        "deal_priorities": [
            "Conduct partner due diligence — confirm brand's prior artist partnership track record, payment reliability, and creative approval process timeline before committing. Partner Quality is the most consequential unassessed dimension.",
            "Obtain deal term sheet — category exclusivity scope, kill fee structure, artist exit right, and creative approval SLAs are all required for a complete DQS assessment. Current structure scoring is LOW confidence on these dimensions.",
            "Assess opportunity cost — identify alternative brand partnerships available in the same category within the next 6 months and confirm whether this deal's exclusivity provisions foreclose deals of comparable or greater value."
        ],
        "structural_flags": [
            "Kill fee status unconfirmed — require before any commitment. A paid brand deal without a kill fee places all cancellation risk on the artist.",
            "Morality clause scope not assessed — require specific trigger language for LEX-CIPHER review before commitment.",
            "Category exclusivity scope not defined — require specific category definition. Over-broad exclusivity is a Dim-5 risk and a Dim-7 opportunity cost driver."
        ],
        "lex_cipher_routing": "Route to LEX-CIPHER when: (1) deal term sheet is available for review, (2) morality clause language is confirmed, (3) IP ownership provisions on content created for the deal are defined. Do not commit before LEX-CIPHER review.",
        "confidence_cap": "Composite confidence capped at LOW: Partner Quality (Dim-3) scored INFERRED — no diligence conducted. Deal Structure (Dim-4) and Risk Exposure (Dim-5) scored LOW — deal documents not yet reviewed. Assessment cannot be confidently scored above Amber band without these inputs.",
        "next_best_action": "Obtain the brand's deal term sheet and conduct a reference check with at least one prior artist partnership — these two inputs would move Partner Quality and Deal Structure from LOW to PARTIAL and would confirm or clear the Risk Exposure gate."
    },
    "model": "claude-sonnet-4-6",
    "mock_note": "BRAND_CONNECT_MOCK_MODE=true — this is a canned assessment. Set BRAND_CONNECT_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/brand-connect/assess", tags=["brand-connect"])
async def brand_connect_assess(req: BrandConnectAssessRequest):
    """
    Brand partnership deal quality assessment for a PLMKR artist + proposed deal.

    Artist identity is bound from the request payload (artist.name from release/
    track metadata), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When BRAND_CONNECT_MOCK_MODE=true (default), returns a canned scored
    assessment without calling the Anthropic API. Set BRAND_CONNECT_MOCK_MODE=false
    with a valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if BRAND_CONNECT_MOCK_MODE:
        result = dict(_BRAND_CONNECT_MOCK_ASSESSMENT)
        result["artist"] = req.artist.model_dump()
        result["deal"]   = req.deal.model_dump()
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set BRAND_CONNECT_MOCK_MODE=true to use mock mode.")

    system_prompt = build_brand_connect_system_prompt(skills_dir=SKILLS_DIR)

    artist = req.artist
    deal   = req.deal

    user_prompt = f"""You are performing a PLMKR brand partnership deal quality assessment. Use the DQS scoring rubric, partnership strategy frameworks, deal economics, deal structure standards, and output templates from your knowledge base to produce a complete Deal Quality Assessment Memo.

ARTIST PROFILE (from release/track metadata — use this for artist identity):
- Credited artist name: {artist.name}
- Primary genre: {artist.genre}
- Career stage: {artist.stage}
- Primary territory: {artist.territory}
- Artist tier: {artist.tier}
- Monthly listeners: {artist.monthly_listeners if artist.monthly_listeners is not None else 'NOT PROVIDED — mark as NOT EVALUABLE'}
- Social following (cross-platform): {artist.social_following if artist.social_following is not None else 'NOT PROVIDED'}
- Engagement rate: {f'{artist.engagement_rate:.1%}' if artist.engagement_rate is not None else 'NOT PROVIDED'}

PROPOSED DEAL DETAILS:
- Deal type: {deal.deal_type}
- Partner category: {deal.partner_category}
- Category exclusivity: {deal.exclusivity_category or 'NOT CONFIRMED'}
- Term: {f'{deal.term_months} months' if deal.term_months is not None else 'NOT CONFIRMED'}
- Kill fee confirmed: {deal.has_kill_fee if deal.has_kill_fee is not None else 'NOT CONFIRMED'}
- Upfront payment %: {f'{deal.upfront_payment_pct:.0%}' if deal.upfront_payment_pct is not None else 'NOT CONFIRMED'}
- Diligence status: {deal.diligence_status}
- Prior artist partnerships (brand's documented history): {deal.prior_artist_deals if deal.prior_artist_deals is not None else 'NOT CONFIRMED'}
- Morality clause present: {deal.has_morality_clause if deal.has_morality_clause is not None else 'NOT CONFIRMED'}
- Morality clause specifically scoped: {deal.morality_clause_scoped if deal.morality_clause_scoped is not None else 'NOT CONFIRMED'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST PROFILE above, not any other name or account reference.
2. Score all 8 DQS dimensions independently. For each, state evidence type (observed / told / inferred), confidence (high / medium / low), and whether the dimension is EVALUABLE from the data above.
3. If a required data field is NOT CONFIRMED or NOT PROVIDED, mark it NOT EVALUABLE — do not estimate or infer it.
4. Apply the DQS composite formula. Label the composite PROVISIONAL with the unlock condition.
5. State both hard gate statuses (Partner Quality Gate, Risk & Exposure Gate) — CLEAR or CONDITIONAL or TRIGGERED with specific reason.
6. Name the top 3 deal priorities (actions the artist should take before committing).
7. Identify any structural flags (terms requiring LEX-CIPHER review before commitment).
8. State the single next best action (24–72h).
9. Do not use probability percentage language for any projection. Label all projections ESTIMATE with the comparable that produced them.
10. Dim-1 (Strategic Value) and Dim-2 (Economic Value) must be scored and reported independently — never collapse them into a single "deal value" judgment.
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=6000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Brand partnership assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist":          req.artist.model_dump(),
        "deal":            req.deal.model_dump(),
        "assessment_text": assessment_text,
        "model":           MODEL_SONNET,
    }


# ── SYNC-AGENT — Sync Licensing Assessment ────────────────────────────────────

class SyncAgentTrackInput(BaseModel):
    """Track-level fields for the sync licensing assessment."""
    title:               str
    genre:               str
    clearance_status:    str   = "UNKNOWN"   # CLEARED|CLEARABLE|PENDING|BLOCKED|UNKNOWN
    is_one_stop:         bool  = False
    has_stems:           bool  = False
    has_clean_version:   bool  = True
    duration_sec:        Optional[float] = None
    bpm:                 Optional[float] = None
    has_samples:         bool  = False
    has_explicit_lyrics: bool  = False

class SyncAgentBriefInput(BaseModel):
    """Brief-level fields describing the sync opportunity."""
    project_type:         str          = "unknown"   # film|tv|ad|trailer|game|web|unknown
    scene_description:    str          = ""
    budget_range:         Optional[str] = None        # e.g., "$5k-$15k" or None
    deadline_days:        Optional[int] = None
    territory:            str          = "worldwide"
    reference_tracks:     list[str]    = []
    lyric_restrictions:   list[str]    = []
    exclusivity_required: bool         = False
    buyer_class:          str          = "unknown"   # indie|mid-tier|major|streaming|ad-agency|unknown

class SyncAgentAssessRequest(BaseModel):
    artist_id:        str   = ""
    artist_name:      str
    artist_territory: str   = "unknown"
    track:            SyncAgentTrackInput
    brief:            SyncAgentBriefInput
    additional_notes: str   = ""

_SYNC_AGENT_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist_name": None,  # filled at runtime
    "track": None,        # filled at runtime
    "brief": None,        # filled at runtime
    "assessment": {
        "dimensions": {
            "brief_fit": {
                "score": 4, "weight": 0.40, "confidence": "PARTIAL",
                "rationale": "Track genre and energy profile consistent with the brief's emotional function. Reference tracks share up-tempo, cinematic qualities with this catalog entry. One defensible deviation: era may differ from references by ~5 years.",
                "not_evaluable": [
                    "lyric theme alignment — no lyric content provided",
                    "specific reference track shared properties — references not yet decoded"
                ]
            },
            "clearance_complexity": {
                "score": 5, "weight": 0.25, "confidence": "HIGH",
                "rationale": "One-stop confirmed: artist controls both master and publishing. No samples or uncleared interpolations flagged. Status: CLEARED — instant yes available.",
                "not_evaluable": []
            },
            "turnaround_feasibility": {
                "score": 4, "weight": 0.20, "confidence": "HIGH",
                "rationale": "One-stop catalog can confirm same-day. Deadline of 14 days met with ≥50% buffer. Structurally eligible for this buyer class.",
                "not_evaluable": []
            },
            "fee_tier": {
                "score": 3, "weight": 0.15, "confidence": "LOW",
                "rationale": "Budget range sits within the standard band for this use category per indicative estimates. Standard negotiation — no strategic exception required.",
                "not_evaluable": [
                    "buyer budget ceiling — no exact figure provided",
                    "comparable closed deals in this category — real comparables pending"
                ]
            }
        },
        "composite": {
            "value": 82,
            "formula": "(4×0.40×20) + (5×0.25×20) + (4×0.20×20) + (3×0.15×20)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked sync assessments in feedback/outcomes/"
        },
        "hard_gates": {
            "clearance_unknown_gate": "CLEAR — clearance status CLEARED; chain fully papered",
            "turnaround_gate":        "CLEAR — turnaround feasibility scored 4; deadline met with ≥50% buffer",
            "brief_fit_gate":         "CLEAR — brief fit scored 4; above the do-not-pitch floor of ≤2"
        },
        "verdict": "PITCH",
        "pitch_rationale": "All three hard gates clear. Composite 82/100 (PROVISIONAL). One-stop clears the clearance risk entirely; brief-fit at 4 gives a defensible one-line fit case. Fee tier confidence is LOW pending exact budget confirmation — quote inside stated budget range or open at top of comparable-supported band.",
        "next_action": "Prepare pitch email within 24h. Lead with clearance status and one-line fit case referencing the scene's emotional function. Include stems availability note. Subject line should carry the answer."
    },
    "mock_note": "SYNC_AGENT_MOCK_MODE=true — this is a canned assessment. Set SYNC_AGENT_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/sync-agent/assess", tags=["sync-agent"])
async def sync_agent_assess(req: SyncAgentAssessRequest):
    """
    Sync licensing brief-fit assessment for a PLMKR artist + track + brief.

    Artist identity is bound from the request payload (artist_name from
    track/release metadata), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When SYNC_AGENT_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set SYNC_AGENT_MOCK_MODE=false with a
    valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if SYNC_AGENT_MOCK_MODE:
        result = dict(_SYNC_AGENT_MOCK_ASSESSMENT)
        result["artist_name"] = req.artist_name
        result["track"]       = req.track.model_dump()
        result["brief"]       = req.brief.model_dump()
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set SYNC_AGENT_MOCK_MODE=true to use mock mode.")

    system_prompt = build_sync_agent_system_prompt(skills_dir=SKILLS_DIR)

    track = req.track
    brief = req.brief

    user_prompt = f"""You are performing a PLMKR sync licensing assessment. Use the scoring rubric, buyer psychology, clearance workflow, deal logic, and output templates from your knowledge base to produce a complete Brief-Fit Scorecard.

ARTIST PROFILE (use this for artist identity — not any account name):
- Credited artist name: {req.artist_name}
- Primary territory: {req.artist_territory}

TRACK DETAILS:
- Title: {track.title}
- Genre: {track.genre}
- Clearance status: {track.clearance_status}
- One-stop (artist controls both master and publishing): {'YES' if track.is_one_stop else 'NO — publishing side requires separate clearance'}
- Stems available: {'YES' if track.has_stems else 'NO'}
- Clean version available: {'YES' if track.has_clean_version else 'NO'}
- Duration: {f'{track.duration_sec:.0f}s' if track.duration_sec is not None else 'NOT PROVIDED'}
- BPM: {f'{track.bpm:.0f}' if track.bpm is not None else 'NOT PROVIDED'}
- Contains samples: {'YES — recursive chain applies; status cannot exceed CLEARABLE until sample chain confirmed' if track.has_samples else 'NO'}
- Explicit lyrics: {'YES — clean version required for most TV/ad; confirm availability' if track.has_explicit_lyrics else 'NO'}

BRIEF DETAILS:
- Project type: {brief.project_type}
- Scene / emotional function: {brief.scene_description or 'NOT PROVIDED — mark brief fit as NOT EVALUABLE from scene function'}
- Budget range: {brief.budget_range or 'NOT PROVIDED — fee tier scored LOW confidence'}
- Deadline (days from now): {brief.deadline_days if brief.deadline_days is not None else 'NOT PROVIDED — turnaround feasibility scored LOW confidence'}
- Territory: {brief.territory}
- Reference tracks: {', '.join(brief.reference_tracks) if brief.reference_tracks else 'NOT PROVIDED'}
- Lyric restrictions: {', '.join(brief.lyric_restrictions) if brief.lyric_restrictions else 'None stated'}
- Exclusivity required: {'YES' if brief.exclusivity_required else 'NO'}
- Buyer class: {brief.buyer_class}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST PROFILE above.
2. Score all 4 rubric dimensions. For each: score (1–5), weight, rationale (1–3 sentences), confidence (HIGH/PARTIAL/LOW), and NOT EVALUABLE items named.
3. If clearance_status is UNKNOWN: cap composite at 40 and flag the gate.
4. Apply the composite formula: Σ(weight × score × 20) → 0–100. Label PROVISIONAL with unlock condition.
5. State all three hard gates: CLEAR or TRIGGERED with reason.
6. Issue verdict: PITCH (≥60, all gates clear, brief_fit ≥ 3) / HOLD / PASS.
7. State ALTERNATIVES if HOLD or PASS (what condition changes the verdict).
8. State the single NEXT BEST ACTION (24–48h).
9. Log as a falsifiable prediction with outcome check date (90 days default).
10. Do not use probability percentage language.
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Sync licensing assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist_name":     req.artist_name,
        "track":           req.track.model_dump(),
        "brief":           req.brief.model_dump(),
        "assessment_text": assessment_text,
        "model":           MODEL_SONNET,
    }


# ── LEX-CIPHER — Legal Deal / Document Quality Assessment ─────────────────────

class LexCipherAgreementInput(BaseModel):
    """Structured description of the agreement under review.

    The agent reviews what is PRESENT and flags what is ABSENT — absence of a
    required provision is itself evaluable as a gap. These flags describe the
    document's structure; they are not legal conclusions.
    """
    agreement_type:               str  = "unknown"   # recording|publishing|management|sync|brand|performance|nda|other
    parties_described:            str  = ""
    governing_territory:          str  = "unknown"
    # Dimension 1 — Rights Grant Clarity
    has_rights_grant:             bool = False
    rights_grant_defined:         bool = False        # territory/term/media/exclusivity specified
    reserved_rights_stated:       bool = False
    # Dimension 2 — Compensation Structure
    compensation_defined:         bool = False
    royalty_base:                 Optional[str] = None  # SRLP|PPD|net_receipts|gross|flat_fee|None
    deductions_defined:           bool = False
    accounting_period_defined:    bool = False
    # Dimension 3 — Recoupment / Cost Transparency
    recoupable_costs_enumerated:  Optional[bool] = None
    cross_collateralization:      Optional[bool] = None
    # Dimension 4 — Exit / Reversion
    has_termination_for_cause:    bool = False
    has_reversion_clause:         bool = False
    perpetual_term:               Optional[bool] = None
    # Dimension 5 — Audit Rights
    has_audit_rights:             bool = False
    audit_window_months:          Optional[int] = None
    # Dimension 6 — Warranties & Representations
    has_ip_ownership_warranty:    bool = False
    has_indemnification:          bool = False
    # Dimension 7 — Dispute Resolution
    governing_law_stated:         bool = False
    dispute_forum_defined:        bool = False
    # Dimension 8 — Red-Flag Clauses
    red_flag_clauses:             list[str] = []      # named clauses present, e.g. "open-ended recoupable costs"

class LexCipherAssessRequest(BaseModel):
    artist_id:        str = ""
    artist_name:      str
    artist_territory: str = "unknown"
    agreement:        LexCipherAgreementInput
    additional_notes: str = ""

_LEX_CIPHER_COUNSEL_FOOTER = (
    "Route to qualified entertainment counsel for execution, negotiation, and legal opinion."
)

_LEX_CIPHER_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist_name": None,   # filled at runtime
    "agreement": None,     # filled at runtime
    "domain_constraint": "Drafts and flags — never advises. Qualified counsel signs off.",
    "assessment": {
        "agreement_type": None,  # filled at runtime
        "dimensions": {
            "rights_grant_clarity": {
                "grade": "B", "numeric": 8.0, "weight": 0.18, "confidence": "PARTIAL",
                "rationale": "Rights grant present with territory, term, and media defined; exclusivity stated. Reserved rights are not separately enumerated — one element requires interpretation but is resolvable from context.",
                "sub_signals": "territory SOURCED · term SOURCED · media SOURCED · exclusivity SOURCED · reserved rights ABSENT",
                "not_evaluable": ["full rights-scope language — only structural flags supplied, not the clause text"]
            },
            "compensation_structure": {
                "grade": "B-", "numeric": 7.5, "weight": 0.16, "confidence": "PARTIAL",
                "rationale": "Compensation type and royalty base defined; accounting period present. Deduction categories are not fully enumerated, leaving the effective rate partly indeterminate without the deduction schedule.",
                "sub_signals": "payment type SOURCED · royalty base SOURCED · deductions AMBIGUOUS · accounting period SOURCED",
                "not_evaluable": ["effective rate — meaningless without the full deduction schedule"]
            },
            "recoupment_transparency": {
                "grade": "C", "numeric": 6.0, "weight": 0.14, "confidence": "PARTIAL",
                "rationale": "Recoupable-cost categories are partially defined; cross-collateralization is present without a stated scope limit. Document this — a cross-collateralization clause without scope nets balances across projects.",
                "sub_signals": "recoupable costs AMBIGUOUS · cross-collateralization SOURCED (scope ABSENT)",
                "not_evaluable": []
            },
            "exit_reversion": {
                "grade": "B", "numeric": 8.0, "weight": 0.13, "confidence": "HIGH",
                "rationale": "Termination for cause is defined and a reversion clause is present with stated trigger conditions. Term is not perpetual.",
                "sub_signals": "termination for cause SOURCED · reversion trigger SOURCED · perpetual term ABSENT",
                "not_evaluable": []
            },
            "audit_rights": {
                "grade": "B-", "numeric": 7.5, "weight": 0.13, "confidence": "HIGH",
                "rationale": "Audit rights present with a window of at least 12 months from statement date by industry convention; scope and cost allocation not fully specified.",
                "sub_signals": "audit clause SOURCED · window SOURCED · scope AMBIGUOUS · cost allocation ABSENT",
                "not_evaluable": []
            },
            "warranties_representations": {
                "grade": "B-", "numeric": 7.5, "weight": 0.12, "confidence": "PARTIAL",
                "rationale": "IP-ownership warranty and an indemnification provision are present. Indemnification proportionality (cap vs. unlimited) and survival are not specified in the supplied flags.",
                "sub_signals": "ownership warranty SOURCED · indemnification SOURCED · proportionality AMBIGUOUS · survival ABSENT",
                "not_evaluable": ["indemnification cap — not described in the structured input"]
            },
            "dispute_resolution": {
                "grade": "C+", "numeric": 6.5, "weight": 0.08, "confidence": "PARTIAL",
                "rationale": "Governing law is stated; forum/jurisdiction is defined. Cost allocation and confidentiality of proceedings are not addressed in the supplied structure.",
                "sub_signals": "governing law SOURCED · forum SOURCED · cost allocation ABSENT · confidentiality ABSENT",
                "not_evaluable": []
            },
            "red_flag_absence": {
                "grade": "B", "numeric": 8.0, "weight": 0.06, "confidence": "HIGH",
                "rationale": "No high-severity red-flag clauses identified in the supplied list. Cross-collateralization without scope limit is documented under recoupment but is not an HG-4 trigger on its own.",
                "sub_signals": "no HG-4 red-flag clauses named",
                "not_evaluable": []
            }
        },
        "hard_gates": {
            "rights_grant_gate":  "CLEAR — rights grant present and defined (HG-1 not triggered)",
            "audit_rights_gate":  "CLEAR — audit rights present with window ≥ 12 months from statement (HG-2 not triggered)",
            "ip_ownership_gate":  "CLEAR — IP-ownership warranty present; chain of title established within stated context (HG-3 not triggered)",
            "red_flag_gate":      "CLEAR — no HG-4 red-flag clause present"
        },
        "composite": {
            "value": 7.4,
            "formula": "(8.0×0.18)+(7.5×0.16)+(6.0×0.14)+(8.0×0.13)+(7.5×0.13)+(7.5×0.12)+(6.5×0.08)+(8.0×0.06)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked deal evaluations in feedback/outcomes/"
        },
        "risk_classification": "NOTABLE_GAPS",
        "red_flags": [
            {
                "clause": "Cross-collateralization without stated scope limit",
                "what_it_does": "Nets recoupable balances across projects so a profitable project pays down another's deficit.",
                "severity": "HIGH",
                "routing": "Identify the deficiency for qualified counsel; route the negotiation position to the management function. Not prescribed here."
            }
        ],
        "not_evaluable": [
            "Full clause text — this assessment is built from structured presence/absence flags, not the agreement itself. A definitive review requires the executed document."
        ],
        "next_best_action": "Provide the executed agreement text for a clause-level review. The single highest-value documentation step is confirming the deduction schedule and the cross-collateralization scope; route any negotiation of those terms to the management function plus qualified counsel.",
        "counsel_footer": _LEX_CIPHER_COUNSEL_FOOTER
    },
    "mock_note": "LEX_CIPHER_MOCK_MODE=true — this is a canned assessment. Set LEX_CIPHER_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/lex-cipher/assess", tags=["lex-cipher"])
async def lex_cipher_assess(req: LexCipherAssessRequest):
    """
    Legal deal / document quality assessment for a PLMKR artist's agreement.

    The agent DRAFTS and FLAGS — it never advises, never gives a legal opinion,
    and never recommends a negotiation position. It scores the eight-dimension
    Deal/Document Quality Rubric, states the four hard gates, classifies legal
    risk severity, and routes execution to qualified entertainment counsel.

    Artist identity is bound from the request payload (artist_name from the
    deal/release context), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When LEX_CIPHER_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set LEX_CIPHER_MOCK_MODE=false with a
    valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if LEX_CIPHER_MOCK_MODE:
        result = dict(_LEX_CIPHER_MOCK_ASSESSMENT)
        result["artist_name"] = req.artist_name
        result["agreement"]   = req.agreement.model_dump()
        # deep-copy the assessment block so per-request fields don't mutate the template
        assessment = dict(result["assessment"])
        assessment["agreement_type"] = req.agreement.agreement_type
        result["assessment"] = assessment
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set LEX_CIPHER_MOCK_MODE=true to use mock mode.")

    system_prompt = build_lex_cipher_system_prompt(skills_dir=SKILLS_DIR)

    ag = req.agreement

    user_prompt = f"""You are performing a PLMKR legal deal/document quality assessment. You DRAFT and FLAG — you never advise, never give a legal opinion, and never recommend a negotiation position. Use the eight-dimension Deal/Document Quality Rubric, the hard gates, and the Contract/Deal Review template from your knowledge base.

ARTIST IDENTITY (use this — not any account name):
- Credited artist name: {req.artist_name}
- Artist territory: {req.artist_territory}

AGREEMENT UNDER REVIEW (structured presence/absence flags — the full clause text is NOT supplied):
- Agreement type: {ag.agreement_type}
- Parties: {ag.parties_described or 'NOT DESCRIBED'}
- Governing territory: {ag.governing_territory}
- Rights grant present: {'YES' if ag.has_rights_grant else 'NO — HG-1 candidate'}
- Rights grant defined (territory/term/media/exclusivity): {'YES' if ag.rights_grant_defined else 'NO'}
- Reserved rights stated: {'YES' if ag.reserved_rights_stated else 'NO'}
- Compensation defined: {'YES' if ag.compensation_defined else 'NO'}
- Royalty base: {ag.royalty_base or 'NOT STATED — effective rate not determinable'}
- Deductions defined: {'YES' if ag.deductions_defined else 'NO'}
- Accounting period defined: {'YES' if ag.accounting_period_defined else 'NO'}
- Recoupable costs enumerated: {ag.recoupable_costs_enumerated if ag.recoupable_costs_enumerated is not None else 'NOT STATED'}
- Cross-collateralization present: {ag.cross_collateralization if ag.cross_collateralization is not None else 'NOT STATED'}
- Termination for cause present: {'YES' if ag.has_termination_for_cause else 'NO'}
- Reversion clause present: {'YES' if ag.has_reversion_clause else 'NO'}
- Perpetual term: {ag.perpetual_term if ag.perpetual_term is not None else 'NOT STATED'}
- Audit rights present: {'YES' if ag.has_audit_rights else 'NO — HG-2 candidate'}
- Audit window (months from statement): {ag.audit_window_months if ag.audit_window_months is not None else 'NOT STATED'}
- IP-ownership warranty present: {'YES' if ag.has_ip_ownership_warranty else 'NO — HG-3 candidate'}
- Indemnification present: {'YES' if ag.has_indemnification else 'NO'}
- Governing law stated: {'YES' if ag.governing_law_stated else 'NO'}
- Dispute forum defined: {'YES' if ag.dispute_forum_defined else 'NO'}
- Named red-flag clauses present: {', '.join(ag.red_flag_clauses) if ag.red_flag_clauses else 'None named'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST IDENTITY above.
2. Score all 8 rubric dimensions. For each: letter grade, numeric equivalent, weight, sub-signal classification (SOURCED/ABSENT/AMBIGUOUS/NOT EVALUABLE), confidence, and a 1–3 sentence rationale describing what the clause does — not what position to take.
3. State all four hard gates (HG-1 Rights Grant, HG-2 Audit Rights, HG-3 IP Ownership, HG-4 Red-Flag Clause): CLEAR or TRIGGERED with reason. An absent rights grant, absent audit rights, audit window shorter than 12 months from statement, unestablished IP ownership, or any high-severity red-flag clause triggers the corresponding gate.
4. Compute the PROVISIONAL COMPOSITE per the rubric formula. Label it PROVISIONAL and state the unlock condition. Treat any retention/threshold figure as industry convention, not a recommendation.
5. Classify legal-risk severity descriptively (LOW_RISK / NOTABLE_GAPS / SIGNIFICANT_GAPS / MATERIALLY_DEFICIENT / CRITICALLY_DEFICIENT). This labels severity — it is NOT a recommendation to sign or walk away.
6. List red-flag clauses present: clause, what it does, severity, and routing. Name the deficiency only — never prescribe a target term or position.
7. Mark NOT EVALUABLE items (the full clause text is not supplied) and name the minimum data required.
8. State a single NEXT BEST ACTION focused on documentation/counsel — route all negotiation to the management function plus qualified counsel.
9. Do not state any rate, advance, or fee as "market standard" without a Tier A/B source.
10. End with the counsel footer: "{_LEX_CIPHER_COUNSEL_FOOTER}"
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Legal assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist_name":     req.artist_name,
        "agreement":       req.agreement.model_dump(),
        "assessment_text": assessment_text,
        "counsel_footer":  _LEX_CIPHER_COUNSEL_FOOTER,
        "model":           MODEL_SONNET,
    }


# ── TOUR-COMMANDER — Tour Campaign Quality Assessment ─────────────────────────

class TourCampaignInput(BaseModel):
    """Structured description of the tour campaign under review.

    The agent scores what is PRESENT and flags what is ABSENT — absence of a
    required planning step (a break-even model, a confirmed anchor, a production
    advance) is itself evaluable as a gap. These flags describe the campaign's
    planning state; they are not predictions of box-office outcome.
    """
    campaign_name:                    str  = ""
    tour_type:                        str  = "headline"   # headline|support|festival_run|one_off|international
    markets_count:                    int  = 0
    has_international_dates:           bool = False
    # Dimension 1 — Routing Logic
    anchor_dates_confirmed:           bool = False
    routing_efficiency_ratio:         Optional[float] = None   # show days / total tour days
    dead_legs_analyzed:               bool = False
    # Dimension 2 — Financial Model Integrity
    break_even_model_exists:          bool = False
    modeled_before_routing:           bool = False
    sensitivity_scenarios_modeled:    bool = False            # 70/85/100% capacity
    # Dimension 3 — Offer Evaluation Quality
    offers_evaluated_against_framework: bool = False
    split_points_analyzed:            Optional[bool] = None
    red_flag_clauses_identified:      bool = False
    # Dimension 4 — Production Readiness
    rider_complete:                   bool = False
    production_advance_completed:     bool = False
    advance_lead_weeks:               Optional[int] = None
    # Dimension 5 — Ticketing Strategy
    price_points_market_analyzed:     bool = False
    tier_structure_defined:           bool = False            # GA + mid + VIP
    secondary_market_monitored:       bool = False
    # Dimension 6 — International Readiness
    work_permits_confirmed:           Optional[bool] = None
    withholding_modeled:              Optional[bool] = None
    territory_streaming_signal:       Optional[bool] = None
    # Dimension 7 — Merch Planning
    merch_planned:                    bool = False
    hall_fees_documented:             bool = False
    # Dimension 8 — Settlement Process
    settlement_review_process:        bool = False
    red_flag_clauses:                 list[str] = []          # named red-flag clauses present in offers

class TourCommanderAssessRequest(BaseModel):
    artist_id:        str = ""
    artist_name:      str
    artist_territory: str = "unknown"
    campaign:         TourCampaignInput
    additional_notes: str = ""

_TOUR_COMMANDER_ADVISORY_FOOTER = (
    "Operational assessment only — not legal, tax, or immigration advice. "
    "Route contracts and work permits to qualified counsel; route detailed "
    "financial modeling to the finance function."
)

_TOUR_COMMANDER_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist_name": None,   # filled at runtime
    "campaign": None,      # filled at runtime
    "operating_principle": "Model first, route second, commit third. Scores planning state — not box-office outcome.",
    "assessment": {
        "tour_type": None,  # filled at runtime
        "dimensions": {
            "routing_logic": {
                "grade": "B", "numeric": 3.0, "weight": 0.20, "confidence": "MEDIUM",
                "rationale": "Anchor-first protocol evident and dead legs analyzed; routing efficiency ratio sits in the adequate band rather than the efficient band. Sequence is defensible but carries some geography-driven fill dates.",
                "sub_signals": "anchors confirmed SOURCED · dead legs analyzed SOURCED · efficiency ratio MEASURED (adequate band) · market sequence JUDGED",
                "not_evaluable": []
            },
            "financial_model_integrity": {
                "grade": "A-", "numeric": 3.7, "weight": 0.20, "confidence": "HIGH",
                "rationale": "A complete break-even model exists and was built before routing was locked, with 70/85/100% sensitivity scenarios. One expense category is estimated without a firm basis.",
                "sub_signals": "break-even model SOURCED · modeled before routing SOURCED · sensitivity scenarios SOURCED · one expense estimate JUDGED",
                "not_evaluable": []
            },
            "offer_evaluation_quality": {
                "grade": "B", "numeric": 3.0, "weight": 0.15, "confidence": "MEDIUM",
                "rationale": "Offers evaluated against the framework with red-flag clauses identified; split-point reachability checked on most but not all backend offers. No below-threshold offer accepted without rationale.",
                "sub_signals": "framework applied SOURCED · red-flags identified SOURCED · split-point analysis AMBIGUOUS (partial)",
                "not_evaluable": []
            },
            "production_readiness": {
                "grade": "B+", "numeric": 3.3, "weight": 0.15, "confidence": "HIGH",
                "rationale": "Rider complete and appropriate to deal level; production advance completed with adequate lead time. Minor discrepancies expected to resolve before show week.",
                "sub_signals": "rider complete SOURCED · advance completed SOURCED · advance lead MEASURED (≥2 weeks)",
                "not_evaluable": []
            },
            "ticketing_strategy": {
                "grade": "B-", "numeric": 2.7, "weight": 0.12, "confidence": "MEDIUM",
                "rationale": "Tier structure defined and secondary market monitored, but pricing is applied with limited market-by-market analysis. Accessible GA floor maintained.",
                "sub_signals": "tier structure SOURCED · secondary monitored SOURCED · market-by-market price analysis AMBIGUOUS",
                "not_evaluable": []
            },
            "international_readiness": {
                "grade": "B-", "numeric": 2.7, "weight": 0.08, "confidence": "MEDIUM",
                "rationale": "International leg has a confirmed work-permit pathway and a territory streaming signal; withholding tax is not yet fully modeled in the P&L. Treat permit and tax specifics as routed to counsel.",
                "sub_signals": "work permit pathway SOURCED · territory streaming signal SOURCED · withholding modeling AMBIGUOUS",
                "not_evaluable": ["definitive withholding rates and treaty relief — route to the finance function and qualified tax counsel"]
            },
            "merch_planning": {
                "grade": "B", "numeric": 3.0, "weight": 0.06, "confidence": "MEDIUM",
                "rationale": "Merch planned and on track for tour start; hall fees documented for most venues. Per-market inventory plan is partial.",
                "sub_signals": "merch planned SOURCED · hall fees documented SOURCED (most venues) · per-market inventory JUDGED",
                "not_evaluable": []
            },
            "settlement_process": {
                "grade": "B", "numeric": 3.0, "weight": 0.04, "confidence": "MEDIUM",
                "rationale": "A line-by-line settlement review process is in place against the deal memo with a dispute protocol. Tour-wide tracking is being maintained.",
                "sub_signals": "review process SOURCED · dispute protocol SOURCED · tour-wide tracking JUDGED",
                "not_evaluable": []
            }
        },
        "hard_gates": {
            "break_even_gate":       "CLEAR — break-even model built before routing commitment (HG-1 not triggered)",
            "anchor_dates_gate":     "CLEAR — top anchor markets confirmed before secondary routing fill (HG-2 not triggered)",
            "work_permit_gate":      "CLEAR — work-permit pathway confirmed for the international leg (HG-3 not triggered)",
            "production_advance_gate": "CLEAR — production advance completed ≥2 weeks before every show (HG-4 not triggered)"
        },
        "composite": {
            "value": 3.1,
            "formula": "(3.0×0.20)+(3.7×0.20)+(3.0×0.15)+(3.3×0.15)+(2.7×0.12)+(2.7×0.08)+(3.0×0.06)+(3.0×0.04)",
            "scale": "0.0–4.3 (letter-grade numeric)",
            "label": "PROVISIONAL",
            "band": "Adequate campaign — gaps that reduce efficiency or upside",
            "unlock_condition": "≥30 outcome-checked tour-campaign evaluations"
        },
        "risk_classification": "NOTABLE_GAPS",
        "red_flags": [],
        "action_profile": [
            {"priority": "PRIORITY", "item": "Tighten the routing efficiency ratio into the efficient band by reviewing geography-driven fill dates against the distance-vs-revenue test."},
            {"priority": "OPTIMIZE", "item": "Add market-by-market price analysis before on-sale; the tier structure is set but pricing is not yet market-calibrated."},
            {"priority": "OPTIMIZE", "item": "Complete withholding-tax modeling for the international leg with the finance function before the P&L is treated as final."}
        ],
        "not_evaluable": [
            "Box-office outcome — this assessment scores the campaign's planning state from structured flags, not realized ticket sales. Settlement data closes the loop after the shows."
        ],
        "next_best_action": "Run the distance-vs-revenue test on every geography-driven fill date to lift the routing efficiency ratio, then finalize withholding-tax modeling on the international leg before locking the P&L. Route any work-permit and contract specifics to qualified counsel.",
        "advisory_footer": _TOUR_COMMANDER_ADVISORY_FOOTER
    },
    "mock_note": "TOUR_COMMANDER_MOCK_MODE=true — this is a canned assessment. Set TOUR_COMMANDER_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/tour-commander/assess", tags=["tour-commander"])
async def tour_commander_assess(req: TourCommanderAssessRequest):
    """
    Tour campaign quality assessment for a PLMKR artist's touring plan.

    The agent scores the eight-dimension Tour Campaign Quality Rubric (routing
    logic, financial-model integrity, offer-evaluation quality, production
    readiness, ticketing strategy, international readiness, merch planning,
    settlement process), states the four hard gates, computes a PROVISIONAL
    composite, and classifies campaign risk severity. It scores PLANNING STATE —
    not box-office outcome — and routes contracts, permits, and detailed
    financial modeling to the appropriate functions and qualified counsel.

    Artist identity is bound from the request payload (artist_name from the
    touring context), NOT from the Playmaker account profile, to prevent
    account-name vs. credited-artist mismatches.

    When TOUR_COMMANDER_MOCK_MODE=true (default), returns a canned scored
    assessment without calling the Anthropic API. Set TOUR_COMMANDER_MOCK_MODE=false
    with a valid ANTHROPIC_API_KEY to run a live assessment.
    """
    if TOUR_COMMANDER_MOCK_MODE:
        result = dict(_TOUR_COMMANDER_MOCK_ASSESSMENT)
        result["artist_name"] = req.artist_name
        result["campaign"]    = req.campaign.model_dump()
        # shallow-copy the assessment block so per-request fields don't mutate the template
        assessment = dict(result["assessment"])
        assessment["tour_type"] = req.campaign.tour_type
        result["assessment"] = assessment
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set TOUR_COMMANDER_MOCK_MODE=true to use mock mode.")

    system_prompt = build_tour_commander_system_prompt(skills_dir=SKILLS_DIR)

    c = req.campaign

    intl_line = (
        "International dates in scope — HG-3 applies."
        if c.has_international_dates else
        "No international dates — HG-3 NOT APPLICABLE; Dimension 6 NOT APPLICABLE."
    )

    user_prompt = f"""You are performing a PLMKR tour campaign quality assessment. You score PLANNING STATE — not box-office outcome. Use the eight-dimension Tour Campaign Quality Rubric, the four hard gates, and the Tour Routing Assessment template from your knowledge base.

ARTIST IDENTITY (use this — not any account name):
- Credited artist name: {req.artist_name}
- Artist territory: {req.artist_territory}

CAMPAIGN UNDER REVIEW (structured planning-state flags — not realized sales):
- Campaign name: {c.campaign_name or 'NOT NAMED'}
- Tour type: {c.tour_type}
- Markets in scope: {c.markets_count}
- {intl_line}
- Anchor dates confirmed before fill: {'YES' if c.anchor_dates_confirmed else 'NO — HG-2 candidate'}
- Routing efficiency ratio (show days ÷ total days): {c.routing_efficiency_ratio if c.routing_efficiency_ratio is not None else 'NOT STATED'}
- Dead legs analyzed: {'YES' if c.dead_legs_analyzed else 'NO'}
- Break-even model exists: {'YES' if c.break_even_model_exists else 'NO — HG-1 candidate'}
- Break-even modeled before routing lock: {'YES' if c.modeled_before_routing else 'NO — HG-1 candidate'}
- Sensitivity scenarios (70/85/100%) modeled: {'YES' if c.sensitivity_scenarios_modeled else 'NO'}
- Offers evaluated against the framework: {'YES' if c.offers_evaluated_against_framework else 'NO'}
- Split points analyzed: {c.split_points_analyzed if c.split_points_analyzed is not None else 'NOT STATED'}
- Red-flag clauses identified: {'YES' if c.red_flag_clauses_identified else 'NO'}
- Rider complete: {'YES' if c.rider_complete else 'NO'}
- Production advance completed: {'YES' if c.production_advance_completed else 'NO — HG-4 candidate'}
- Production advance lead (weeks before show): {c.advance_lead_weeks if c.advance_lead_weeks is not None else 'NOT STATED'}
- Price points set with market analysis: {'YES' if c.price_points_market_analyzed else 'NO'}
- Tier structure (GA/mid/VIP) defined: {'YES' if c.tier_structure_defined else 'NO'}
- Secondary market monitored: {'YES' if c.secondary_market_monitored else 'NO'}
- Work permits confirmed (international): {c.work_permits_confirmed if c.work_permits_confirmed is not None else 'NOT STATED'}
- Withholding tax modeled: {c.withholding_modeled if c.withholding_modeled is not None else 'NOT STATED'}
- Territory streaming signal: {c.territory_streaming_signal if c.territory_streaming_signal is not None else 'NOT STATED'}
- Merch planned: {'YES' if c.merch_planned else 'NO'}
- Hall fees documented: {'YES' if c.hall_fees_documented else 'NO'}
- Settlement review process in place: {'YES' if c.settlement_review_process else 'NO'}
- Named red-flag clauses present: {', '.join(c.red_flag_clauses) if c.red_flag_clauses else 'None named'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST IDENTITY above.
2. Score all 8 rubric dimensions. For each: letter grade, numeric equivalent, weight, sub-signal classification (MEASURED/SOURCED/JUDGED/NOT EVALUABLE), confidence band (HIGH/MEDIUM/LOW with reasons), and a 1–3 sentence rationale describing the planning state — not a box-office prediction. If the campaign has no international dates, mark Dimension 6 NOT APPLICABLE.
3. State all four hard gates (HG-1 Break-Even Before Commitment, HG-2 Anchor Before Fill, HG-3 Work-Permit Pathway, HG-4 Production Advance): CLEAR / TRIGGERED / NOT APPLICABLE with reason.
4. Compute the PROVISIONAL COMPOSITE on the 0.0–4.3 letter-grade numeric scale per the rubric formula. Label it PROVISIONAL and state the unlock condition. Treat any threshold figure as industry convention, not a recommendation.
5. Classify campaign risk severity descriptively (LOW_RISK / NOTABLE_GAPS / SIGNIFICANT_GAPS / HIGH_FINANCIAL_RISK / CRITICAL_RISK). This labels severity — it is NOT a recommendation to proceed, hold, or cancel.
6. List named red-flag clauses present: clause, what it does, and routing. Name the deficiency only.
7. Mark NOT EVALUABLE items and name the minimum data required. Never quote a guarantee, production cost, or P&L figure without a Tier A/B source.
8. Provide an Action Profile (IMMEDIATE / PRIORITY / OPTIMIZE / MAINTAIN) and a single NEXT BEST ACTION. Route contracts and permits to qualified counsel and detailed modeling to the finance function.
9. End with the advisory footer: "{_TOUR_COMMANDER_ADVISORY_FOOTER}"
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Tour assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist_name":     req.artist_name,
        "campaign":        req.campaign.model_dump(),
        "assessment_text": assessment_text,
        "advisory_footer": _TOUR_COMMANDER_ADVISORY_FOOTER,
        "model":           MODEL_SONNET,
    }


# ── INK-AND-AIR — Catalog Health (Publishing & Rights) Assessment ─────────────

class CatalogRightsInput(BaseModel):
    """Structured description of the catalog / work under review.

    The agent scores what is PRESENT and flags what is ABSENT — absence of a
    required step (a registration, an executed split sheet, a filed claim) is
    itself evaluable as a gap. These flags describe the catalog's rights state;
    they are not a valuation and not a legal opinion.
    """
    catalog_name:                      str  = ""
    work_count:                        int  = 0
    has_international_usage:            bool = False
    # D1 — Registration Completeness
    pro_registration_complete:         bool = False
    mechanical_registration_complete:  bool = False
    new_works_registered_before_release: bool = False
    # D2 — Collection Coverage
    active_income_streams:             list[str] = []   # performance|mechanical|sync|neighboring|ugc
    ugc_monetization_active:           bool = False
    neighboring_rights_registered:     bool = False
    # D3 — Royalty Recovery Readiness
    mlc_unmatched_claims_filed:        Optional[bool] = None
    black_box_claim_strategy:          bool = False
    # D4 — Identifier Completeness
    iswc_coverage_complete:            bool = False
    ipi_registered_all_parties:        bool = False
    active_revenue_without_identifiers: bool = False     # HG-1 trigger
    # D5 — Ownership Clarity
    split_sheets_executed:             bool = False
    chain_of_title_documented:         bool = False
    active_ownership_dispute:          bool = False       # HG-2 trigger (when formally filed)
    # D6 — Licensing Readiness
    one_stop_clearance:                Optional[bool] = None
    sync_rep_in_place:                 bool = False
    master_rights_clear:               bool = False
    # D7 — Territorial Coverage
    subpublishing_in_major_territories: bool = False
    territories_collecting_count:      int  = 0
    # D8 — Metadata Quality
    statement_matching_rate:           Optional[float] = None  # 0.0–1.0
    # D9 — Audit Status
    audit_window_status:               str  = "unknown"   # within|approaching|expired|unknown
    last_audit_within_window:          bool = False
    # D10 — Legal Exposure
    active_litigation:                 bool = False        # HG-4 trigger
    uncleared_sample_exposure:         Optional[bool] = None

class InkAndAirAssessRequest(BaseModel):
    artist_id:        str = ""
    artist_name:      str
    artist_territory: str = "unknown"
    catalog:          CatalogRightsInput
    additional_notes: str = ""

_INK_AND_AIR_ADVISORY_FOOTER = (
    "This is a publishing rights-infrastructure assessment — not a legal opinion, "
    "a financial valuation, or a sync-pitch strategy. Route deal execution and notice "
    "filing to qualified entertainment counsel, royalty modeling to the Finance/Royalties "
    "function, and sync pursuit to the Sync agent."
)

_INK_AND_AIR_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist_name": None,   # filled at runtime
    "catalog": None,       # filled at runtime
    "domain_constraint": "Maximizes legitimate royalty capture and rights protection. Identifies and explains; never advises on negotiation, never gives a legal opinion.",
    "assessment": {
        "catalog_name": None,  # filled at runtime
        "dimensions": {
            "registration_completeness": {
                "grade": "B", "numeric": 7.0, "weight": 0.15, "confidence": "PARTIAL",
                "rationale": "PRO registration is present across the home territory and new works are registered before release; mechanical registration shows documented timing gaps on part of the catalog tail. Registration is prospective, not yet a fully closed loop.",
                "sub_signals": "PRO coverage SOURCED · mechanical coverage AMBIGUOUS · new-works lead time SOURCED · black-box-from-gaps NOT EVALUABLE",
                "not_evaluable": ["exact PRO/mechanical coverage percentages — requires a society-portal export, not supplied"]
            },
            "collection_coverage": {
                "grade": "B-", "numeric": 6.5, "weight": 0.15, "confidence": "PARTIAL",
                "rationale": "Performance and mechanical are collecting and at least one UGC platform is monetized; neighboring-rights infrastructure is initiated but not complete across all applicable territories. Gaps are identified with a remediation path.",
                "sub_signals": "performance SOURCED · mechanical SOURCED · UGC SOURCED · neighboring rights AMBIGUOUS",
                "not_evaluable": []
            },
            "royalty_recovery_readiness": {
                "grade": "C", "numeric": 5.0, "weight": 0.13, "confidence": "PARTIAL",
                "rationale": "Recovery mechanisms are largely unworked: MLC unmatched-pool claims are not confirmed filed and there is no active society black-box claim program. This is quantifiable value currently uncaptured — document it as a recovery opportunity.",
                "sub_signals": "MLC unmatched claims AMBIGUOUS · black-box strategy ABSENT · retroactive recovery NOT EVALUABLE",
                "not_evaluable": ["recoverable value — requires statement history and a dated registration-gap range; estimate only where evidence supports it"]
            },
            "identifier_completeness": {
                "grade": "B", "numeric": 7.0, "weight": 0.12, "confidence": "HIGH",
                "rationale": "ISWC coverage and IPI registration for all writers and publishers are in place; no active-revenue works lack identifiers (HG-1 not triggered). Some ISRC linkage gaps remain on older catalog.",
                "sub_signals": "ISWC SOURCED · IPI all parties SOURCED · active-revenue-without-identifiers ABSENT",
                "not_evaluable": []
            },
            "ownership_clarity": {
                "grade": "B+", "numeric": 8.0, "weight": 0.12, "confidence": "HIGH",
                "rationale": "Co-written works carry executed split sheets and chain of title is documented; no formally filed ownership dispute is on record (HG-2 not triggered).",
                "sub_signals": "executed splits SOURCED · chain of title SOURCED · active dispute ABSENT",
                "not_evaluable": []
            },
            "licensing_readiness": {
                "grade": "C+", "numeric": 6.0, "weight": 0.12, "confidence": "PARTIAL",
                "rationale": "Master rights are clear but one-stop clearance is not confirmed and no dedicated sync representative is in place; licensing is possible but happens by ad hoc negotiation. No HG-2 dispute caps this dimension.",
                "sub_signals": "master rights SOURCED · one-stop status AMBIGUOUS · sync rep ABSENT",
                "not_evaluable": ["turnaround capability — not described in the structured input"]
            },
            "territorial_coverage": {
                "grade": "C", "numeric": 5.0, "weight": 0.08, "confidence": "PARTIAL",
                "rationale": "Home territory plus a few majors are collecting via sub-publishing; no direct affiliations in non-Western markets and reciprocal coverage is unverified against streaming territory data.",
                "sub_signals": "sub-pub in majors SOURCED · territory count MEASURED · usage-vs-revenue overlap NOT EVALUABLE",
                "not_evaluable": ["usage-vs-revenue territory overlap — requires DSP territory streaming data"]
            },
            "metadata_quality": {
                "grade": "B-", "numeric": 6.5, "weight": 0.07, "confidence": "PARTIAL",
                "rationale": "Statement matching rate is in the mid-range with minor discrepancies under reconciliation; ISWC is mostly linked in the content-management system.",
                "sub_signals": "matching rate MEASURED · share consistency AMBIGUOUS · ISWC-in-CMS SOURCED",
                "not_evaluable": []
            },
            "audit_status": {
                "grade": "B", "numeric": 7.0, "weight": 0.04, "confidence": "HIGH",
                "rationale": "The contractual audit window is not expired and a statement-review practice is in place (HG-3 not triggered). New-revenue-stream monitoring is reactive rather than systematic.",
                "sub_signals": "audit window SOURCED (not expired) · review practice SOURCED · new-stream monitoring JUDGED",
                "not_evaluable": []
            },
            "legal_exposure": {
                "grade": "A-", "numeric": 8.5, "weight": 0.02, "confidence": "PARTIAL",
                "rationale": "No active infringement litigation names the catalog (HG-4 not triggered) and termination windows are tracked. Uncleared sample exposure is not confirmed either way and is flagged for documentation.",
                "sub_signals": "active litigation ABSENT · termination windows SOURCED · uncleared samples AMBIGUOUS · AI exposure CONTESTED (no settled law)",
                "not_evaluable": ["uncleared sample exposure — not confirmed in the structured input"]
            }
        },
        "hard_gates": {
            "identifier_gate":       "CLEAR — no active-revenue works without ISWC and PRO registration (HG-1 not triggered)",
            "ownership_dispute_gate":"CLEAR — no formally filed ownership dispute on record (HG-2 not triggered)",
            "audit_window_gate":     "CLEAR — contractual audit window not expired (HG-3 not triggered)",
            "litigation_gate":       "CLEAR — no active infringement litigation naming the catalog (HG-4 not triggered)"
        },
        "composite": {
            "value": 6.5,
            "formula": "(7.0×0.15)+(6.5×0.15)+(5.0×0.13)+(7.0×0.12)+(8.0×0.12)+(6.0×0.12)+(5.0×0.08)+(6.5×0.07)+(7.0×0.04)+(8.5×0.02)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked catalog evaluations",
            "note": "PROVISIONAL — not calibrated; not comparable across catalogs. Secondary to the per-dimension grades."
        },
        "risk_classification": "NOTABLE_GAPS",
        "asset_recovery_frame": "If this catalog went to sale, licensing, or audit today, due diligence would discount it primarily on royalty-recovery readiness (unworked unmatched/black-box claims) and territorial coverage (unverified reciprocal collection), with ownership clarity and legal exposure as genuine strengths. The largest near-term upside is filing the recovery claims and verifying foreign collection.",
        "action_profile": {
            "immediate": [],
            "priority": [
                {
                    "dimension": "royalty_recovery_readiness",
                    "gap": "MLC unmatched-pool claims not confirmed filed; no active black-box claim program.",
                    "action": "File MLC unmatched-pool claims (US) and stand up a society black-box claim program; track retroactive recovery windows.",
                    "estimated_recovery": "NOT ESTIMABLE without statement history and a dated registration-gap range — qualitative recoverability only."
                }
            ],
            "optimize": [
                {
                    "dimension": "licensing_readiness",
                    "gap": "One-stop clearance not confirmed; no dedicated sync representative.",
                    "action": "Confirm one-stop clearance authority and establish a rate card / single sync contact; route active sync pursuit to the Sync agent."
                },
                {
                    "dimension": "territorial_coverage",
                    "gap": "Reciprocal coverage unverified against streaming territory data (sub-threshold weight, still improvable).",
                    "action": "Map DSP territory streaming data against statement territories; confirm sub-publisher registration in the top revenue territories."
                }
            ],
            "maintain": [
                "registration_completeness", "collection_coverage", "identifier_completeness",
                "ownership_clarity", "metadata_quality", "audit_status", "legal_exposure"
            ]
        },
        "not_evaluable": [
            "Exact coverage percentages, recoverable value, and territory overlap — this assessment is built from structured presence/absence flags, not from society-portal exports, statements, or DSP territory data. A definitive evaluation requires those records."
        ],
        "next_best_action": "File the MLC unmatched-pool claims and stand up the black-box recovery program — the single highest-value documentation step. Provide 3-year statement history and a society-portal export to convert the PARTIAL-confidence dimensions to a sourced grade. Route any deal negotiation to qualified counsel and royalty modeling to the Finance/Royalties function.",
        "advisory_footer": _INK_AND_AIR_ADVISORY_FOOTER
    },
    "mock_note": "INK_AND_AIR_MOCK_MODE=true — this is a canned assessment. Set INK_AND_AIR_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/ink-and-air/assess", tags=["ink-and-air"])
async def ink_and_air_assess(req: InkAndAirAssessRequest):
    """
    Catalog Health (publishing & rights) assessment for a PLMKR artist's catalog.

    The agent scores the ten-dimension Catalog Health Rubric, states the four hard
    gates, answers the Asset-Recovery Frame, classifies rights-infrastructure risk
    severity, produces a prioritized Action Profile, and routes execution out. It
    identifies and explains — it never advises on negotiation, never gives a legal
    opinion, and never builds a financial valuation.

    Artist identity is bound from the request payload (artist_name from the catalog
    context), NOT from the Playmaker account profile, to prevent account-name vs.
    credited-artist mismatches.

    When INK_AND_AIR_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set INK_AND_AIR_MOCK_MODE=false with a valid
    ANTHROPIC_API_KEY to run a live assessment.
    """
    if INK_AND_AIR_MOCK_MODE:
        result = dict(_INK_AND_AIR_MOCK_ASSESSMENT)
        result["artist_name"] = req.artist_name
        result["catalog"]     = req.catalog.model_dump()
        # shallow-copy the assessment block so per-request fields don't mutate the template
        assessment = dict(result["assessment"])
        assessment["catalog_name"] = req.catalog.catalog_name
        result["assessment"] = assessment
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set INK_AND_AIR_MOCK_MODE=true to use mock mode.")

    system_prompt = build_ink_and_air_system_prompt(skills_dir=SKILLS_DIR)

    cat = req.catalog

    user_prompt = f"""You are performing a PLMKR Catalog Health assessment (publishing & rights). You IDENTIFY and EXPLAIN — you never advise on negotiation, never give a legal opinion, and never build a financial valuation. Use the ten-dimension Catalog Health Rubric, the four hard gates, the Asset-Recovery Frame, and the Catalog Health Evaluation template from your knowledge base.

ARTIST IDENTITY (use this — not any account name):
- Credited artist name: {req.artist_name}
- Artist territory: {req.artist_territory}

CATALOG UNDER REVIEW (structured presence/absence flags — full statements/portal exports are NOT supplied):
- Catalog name: {cat.catalog_name or 'NOT NAMED'}
- Work count: {cat.work_count}
- Has international usage: {'YES' if cat.has_international_usage else 'NO'}
- PRO registration complete: {'YES' if cat.pro_registration_complete else 'NO'}
- Mechanical registration complete: {'YES' if cat.mechanical_registration_complete else 'NO'}
- New works registered before release: {'YES' if cat.new_works_registered_before_release else 'NO'}
- Active income streams: {', '.join(cat.active_income_streams) if cat.active_income_streams else 'None reported'}
- UGC monetization active: {'YES' if cat.ugc_monetization_active else 'NO'}
- Neighboring rights registered: {'YES' if cat.neighboring_rights_registered else 'NO'}
- MLC unmatched-pool claims filed: {cat.mlc_unmatched_claims_filed if cat.mlc_unmatched_claims_filed is not None else 'NOT STATED'}
- Black-box claim strategy in place: {'YES' if cat.black_box_claim_strategy else 'NO'}
- ISWC coverage complete: {'YES' if cat.iswc_coverage_complete else 'NO'}
- IPI registered for all parties: {'YES' if cat.ipi_registered_all_parties else 'NO'}
- Active revenue without identifiers: {'YES — HG-1 candidate' if cat.active_revenue_without_identifiers else 'NO'}
- Split sheets executed: {'YES' if cat.split_sheets_executed else 'NO'}
- Chain of title documented: {'YES' if cat.chain_of_title_documented else 'NO'}
- Active ownership dispute (formally filed): {'YES — HG-2 candidate' if cat.active_ownership_dispute else 'NO'}
- One-stop clearance: {cat.one_stop_clearance if cat.one_stop_clearance is not None else 'NOT STATED'}
- Sync representative in place: {'YES' if cat.sync_rep_in_place else 'NO'}
- Master rights clear: {'YES' if cat.master_rights_clear else 'NO'}
- Sub-publishing in major territories: {'YES' if cat.subpublishing_in_major_territories else 'NO'}
- Territories collecting (count): {cat.territories_collecting_count}
- Statement matching rate: {f'{cat.statement_matching_rate:.0%}' if cat.statement_matching_rate is not None else 'NOT STATED'}
- Audit window status: {cat.audit_window_status}
- Last audit within window: {'YES' if cat.last_audit_within_window else 'NO'}
- Active litigation naming the catalog: {'YES — HG-4 candidate' if cat.active_litigation else 'NO'}
- Uncleared sample exposure: {cat.uncleared_sample_exposure if cat.uncleared_sample_exposure is not None else 'NOT STATED'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST IDENTITY above.
2. Score all 10 rubric dimensions. For each: letter grade, numeric equivalent, weight, sub-signal classification (MEASURED/SOURCED/JUDGED/AMBIGUOUS/ABSENT/NOT EVALUABLE), confidence (HIGH/MEDIUM/LOW/PARTIAL with reason), and a 1–3 sentence rationale describing the economic consequence of the current state — not a negotiation position.
3. State all four hard gates (HG-1 Active Revenue Without Identifiers, HG-2 Unresolved Ownership Dispute, HG-3 Expired Audit Window, HG-4 Active Litigation): CLEAR or TRIGGERED with reason. HG-2 requires a formally filed dispute; a disclosed-but-unfiled dispute is CLEAR but must still be surfaced as a flagged risk.
4. Compute the PROVISIONAL COMPOSITE per the rubric formula. Label it PROVISIONAL and state the unlock condition. Treat any retention/threshold figure as industry convention, not a recommendation.
5. Answer the Asset-Recovery Frame explicitly with evidence from the dimension grades.
6. Classify rights-infrastructure risk severity descriptively (LOW_RISK / NOTABLE_GAPS / SIGNIFICANT_GAPS / MATERIALLY_DEFICIENT / CRITICALLY_DEFICIENT). This labels severity — it is NOT a recommendation to sign, sell, or walk away.
7. Produce an Action Profile (IMMEDIATE / PRIORITY / OPTIMIZE / MAINTAIN), with recoverability estimates ONLY where evidence supports them (labeled ESTIMATE with basis, or NOT ESTIMABLE).
8. Mark NOT EVALUABLE items and name the minimum data required.
9. Do not state any rate, advance, fee, or multiple as "market standard" without a Tier A/B source. Treat AI training-rights questions as contested unless settled.
10. End with the advisory footer: "{_INK_AND_AIR_ADVISORY_FOOTER}"
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Publishing assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist_name":     req.artist_name,
        "catalog":         req.catalog.model_dump(),
        "assessment_text": assessment_text,
        "advisory_footer": _INK_AND_AIR_ADVISORY_FOOTER,
        "model":           MODEL_SONNET,
    }


# ── ROYALTY-DOCTOR — Royalty Recovery Audit ──────────────────────────────────────

class RoyaltyCatalogInput(BaseModel):
    """Structured description of the catalog under recovery review.

    The agent scores the catalog's RECOVERY STATE — how completely it is collecting
    income it has already earned, and how ready it is to recover what it is not.
    Absence of a required step (a registration, a filed claim, a verification
    practice) is itself evaluable as a leak point. These flags are not a valuation
    and not a legal opinion.
    """
    catalog_name:                      str  = ""
    work_count:                        int  = 0
    has_international_usage:            bool = False
    # HG-1 inputs — minimum data set for an evaluable recovery audit
    statement_data_available:          bool = False
    registration_export_available:     bool = False
    # D1 — Registration Integrity
    pro_registration_complete:         bool = False
    mechanical_registration_complete:  bool = False
    neighboring_rights_registered:     bool = False
    identifiers_complete:              bool = False   # ISWC / ISRC / IPI on earning works
    active_revenue_without_identifiers: bool = False
    # D2 — Statement Verification
    statements_verified_against_dsp:   bool = False
    anomaly_review_practiced:          bool = False
    reserve_deductions_reviewed:       bool = False
    # D3 — Black-Box Recovery Readiness
    unmatched_pool_claims_filed:       Optional[bool] = None
    black_box_program_active:          bool = False
    proof_of_ownership_ready:          bool = False
    # D4 — Pipeline Coverage
    active_income_streams:             list[str] = []   # master|performance|mechanical|neighboring|sync_backend
    # D5 — Audit Readiness
    audit_window_status:               str  = "unknown"   # within|approaching|expired|unknown
    statement_history_retained:        bool = False
    soft_audit_practice:               bool = False
    # D6 — Collection-Timing Discipline
    lag_vs_missing_tracked:            bool = False
    # D7 — Recovery Documentation
    chain_of_title_documented:         bool = False
    split_sheets_executed:             bool = False

class RoyaltyDoctorAssessRequest(BaseModel):
    artist_id:        str = ""
    artist_name:      str
    artist_territory: str = "unknown"
    catalog:          RoyaltyCatalogInput
    additional_notes: str = ""

_ROYALTY_DOCTOR_ADVISORY_FOOTER = (
    "This is a royalty-recovery analysis — it identifies and documents where income "
    "is uncollected or underpaid and builds the recovery case. It is not a legal "
    "opinion, a contract interpretation, or a catalog valuation. Route formal audit "
    "demands and any legal action to qualified entertainment counsel, deal and "
    "valuation modeling to the Finance/Royalties function, copyright-law and "
    "publishing-deal questions to the Publishing function, and sync pursuit to the "
    "Sync function."
)

_ROYALTY_DOCTOR_MOCK_ASSESSMENT = {
    "status": "ok",
    "mock": True,
    "artist_name": None,   # filled at runtime
    "catalog": None,       # filled at runtime
    "domain_constraint": "Maximizes legitimate cash capture. Identifies, documents, and quantifies-where-evidence-supports; rules out normal pipeline lag before claiming loss; never fabricates a recoverable figure; never renders a legal opinion.",
    "assessment": {
        "catalog_name": None,  # filled at runtime
        "dimensions": {
            "registration_integrity": {
                "grade": "B-", "numeric": 6.5, "weight": 0.20, "confidence": "PARTIAL",
                "rationale": "PRO registration is complete across the home territory, but mechanical registration shows documented gaps on the catalog tail and neighboring rights are not registered with the applicable collectors. Each gap means earned income that cannot be matched to its owner.",
                "sub_signals": "PRO coverage SOURCED · mechanical coverage AMBIGUOUS · neighboring-rights registration ABSENT · identifier coverage SOURCED",
                "not_evaluable": ["exact PRO/mechanical coverage percentages — requires a society-portal export, not supplied"]
            },
            "statement_verification": {
                "grade": "C+", "numeric": 6.0, "weight": 0.18, "confidence": "PARTIAL",
                "rationale": "Statements receive spot checks but no systematic cross-reference against DSP dashboard data and no full twelve-category anomaly review. The reserve and deduction sections are not routinely reconciled — a common location for silent underpayment.",
                "sub_signals": "DSP cross-reference JUDGED (intermittent) · anomaly checklist JUDGED (not systematic) · reserve/deduction review ABSENT",
                "not_evaluable": []
            },
            "black_box_recovery_readiness": {
                "grade": "C", "numeric": 5.0, "weight": 0.16, "confidence": "PARTIAL",
                "rationale": "Recovery mechanisms are largely unworked: unmatched-pool claims are not confirmed filed and there is no active black-box claim program with the holding collectors. This is quantifiable value currently uncaptured and aging toward redistribution — document it as the primary recovery opportunity.",
                "sub_signals": "unmatched-pool claims AMBIGUOUS · black-box program ABSENT · proof-of-ownership package JUDGED (partial)",
                "not_evaluable": ["recoverable value — requires distribution history and a dated registration-gap range; NOT ESTIMABLE on the supplied flags"]
            },
            "pipeline_coverage": {
                "grade": "B", "numeric": 7.0, "weight": 0.14, "confidence": "PARTIAL",
                "rationale": "Master, performance, and mechanical streams are flowing; neighboring rights and sync backend are not confirmed collecting where international usage exists. The same plays are generating income on streams that are not all being captured.",
                "sub_signals": "master SOURCED · performance SOURCED · mechanical SOURCED · neighboring/sync-backend AMBIGUOUS",
                "not_evaluable": []
            },
            "audit_readiness": {
                "grade": "B", "numeric": 7.0, "weight": 0.12, "confidence": "HIGH",
                "rationale": "The contractual audit window is within range (not expired — HG-4 not triggered) and statement history is retained for the recoverable period. A soft-audit / written-inquiry practice exists but is used reactively rather than as a standing discipline.",
                "sub_signals": "audit window SOURCED (within) · statement history SOURCED · soft-audit practice JUDGED",
                "not_evaluable": []
            },
            "collection_timing_discipline": {
                "grade": "B+", "numeric": 8.0, "weight": 0.10, "confidence": "HIGH",
                "rationale": "The team distinguishes income in normal pipeline transit from income that is genuinely stuck or underpaid, and maps the expected lag per stream before flagging a loss. This keeps recovery claims credible and avoids premature audit demands (HG-3 discipline intact).",
                "sub_signals": "per-stream lag mapping JUDGED · usage-vs-receipt comparison JUDGED · in-transit/stuck/underpaid classification JUDGED",
                "not_evaluable": []
            },
            "recovery_documentation": {
                "grade": "C+", "numeric": 6.0, "weight": 0.10, "confidence": "PARTIAL",
                "rationale": "Chain of title is documented, but split sheets are not executed across all co-written works, leaving ownership ambiguity that would weaken a claim. The evidentiary chain is partial — sufficient for some claims, not yet for all.",
                "sub_signals": "chain of title SOURCED · executed splits AMBIGUOUS · identifier/registration records JUDGED (partial)",
                "not_evaluable": []
            }
        },
        "hard_gates": {
            "data_sufficiency_gate": "CLEAR — statement data and a registration export are available; the audit is evaluable (HG-1 not triggered)",
            "fabrication_gate":      "CLEAR — no recoverable figure is stated without statement history and a dated gap range (HG-2 not triggered)",
            "lag_diagnosis_gate":    "CLEAR — questioned streams are classified IN TRANSIT / STUCK / UNDERPAID before any loss claim (HG-3 not triggered)",
            "audit_window_gate":     "CLEAR — the contractual audit window is not expired for the period in question (HG-4 not triggered)"
        },
        "composite": {
            "value": 6.4,
            "formula": "(6.5×0.20)+(6.0×0.18)+(5.0×0.16)+(7.0×0.14)+(7.0×0.12)+(8.0×0.10)+(6.0×0.10)",
            "label": "PROVISIONAL",
            "unlock_condition": "≥30 outcome-checked recovery audits",
            "note": "PROVISIONAL — not calibrated; not comparable across catalogs. Secondary to the per-dimension grades."
        },
        "recovery_posture": "NOTABLE_LEAKAGE",
        "leak_map": [
            {
                "leak": "Unmatched-pool / black-box mechanicals",
                "evidence": "Unmatched-pool claims not confirmed filed; no active claim program (D3 = C). Registration tail gaps (D1 = B-) feed the unmatched pool.",
                "recoverable": "NOT ESTIMABLE — requires distribution history and a dated registration-gap range. Time-sensitive: unmatched mechanicals are subject to market-share redistribution after a retention period (industry convention)."
            },
            {
                "leak": "Uncollected neighboring rights",
                "evidence": "Neighboring rights not registered with applicable collectors (D1) and not confirmed flowing (D4), despite international usage.",
                "recoverable": "NOT ESTIMABLE on the supplied flags — register, then file the claim with proof of ownership."
            },
            {
                "leak": "Silent statement underpayment (reserve / deductions)",
                "evidence": "Reserve and deduction sections not routinely reconciled (D2 = C+); no systematic DSP cross-reference.",
                "recoverable": "NOT ESTIMABLE without the statements themselves — surfaces through a soft audit citing specific line items."
            }
        ],
        "recovery_plan": {
            "immediate": [],
            "priority": [
                {
                    "dimension": "black_box_recovery_readiness",
                    "gap": "Unmatched-pool claims not filed; no black-box claim program; recoverable money aging toward redistribution.",
                    "action": "Close the mechanical/neighboring registration tail gaps, then file the unmatched-pool and historical claims with proof of ownership; track each retroactive recovery window against its deadline.",
                    "estimated_recovery": "NOT ESTIMABLE without distribution history and a dated registration-gap range — qualitative recoverability only."
                },
                {
                    "dimension": "registration_integrity",
                    "gap": "Mechanical tail gaps and unregistered neighboring rights are causing earned income to go unmatched.",
                    "action": "Complete mechanical registration on the catalog tail and register neighboring rights with the applicable collectors — this stops the leak prospectively and unlocks the retroactive claims."
                }
            ],
            "optimize": [
                {
                    "dimension": "statement_verification",
                    "gap": "Statements spot-checked, not systematically verified; reserve/deduction sections not reconciled.",
                    "action": "Stand up a standing statement-verification practice: DSP cross-reference plus the twelve-category anomaly checklist plus a reserve/deduction reconciliation on every statement; raise anomalies via a documented soft audit before any formal demand."
                },
                {
                    "dimension": "recovery_documentation",
                    "gap": "Split sheets not executed across all co-written works.",
                    "action": "Execute split sheets on the remaining co-written works to complete the evidentiary chain needed to file claims."
                }
            ],
            "maintain": [
                "pipeline_coverage", "audit_readiness", "collection_timing_discipline"
            ]
        },
        "not_evaluable": [
            "Recoverable dollar amounts, exact coverage percentages, and per-stream income — this audit is built from structured presence/absence flags, not from statements, distribution history, or society-portal exports. A definitive recovery figure requires those records plus a dated registration-gap or anomaly range."
        ],
        "next_best_action": "File the unmatched-pool / black-box claims and close the mechanical and neighboring-rights registration tail gaps — the single highest-value, time-sensitive recovery step. Supply 3-year statement history and a society-portal export to convert the PARTIAL-confidence dimensions to sourced grades and to make recoverable amounts estimable. Route any formal audit demand to qualified counsel.",
        "advisory_footer": _ROYALTY_DOCTOR_ADVISORY_FOOTER
    },
    "mock_note": "ROYALTY_DOCTOR_MOCK_MODE=true — this is a canned assessment. Set ROYALTY_DOCTOR_MOCK_MODE=false with a valid ANTHROPIC_API_KEY to run a live assessment."
}


@app.post("/api/agents/royalty-doctor/assess", tags=["royalty-doctor"])
async def royalty_doctor_assess(req: RoyaltyDoctorAssessRequest):
    """
    Royalty Recovery Audit for a PLMKR artist's catalog.

    The agent scores the seven-dimension Royalty Recovery Readiness Rubric, states
    the four hard gates, classifies recovery posture (leakage severity), produces a
    Leak Map and a prioritized Recovery Plan, and routes execution out. It IDENTIFIES,
    DOCUMENTS, and QUANTIFIES-WHERE-EVIDENCE-SUPPORTS — it rules out normal pipeline
    lag before claiming loss, never fabricates a recoverable figure, and never renders
    a legal opinion.

    Artist identity is bound from the request payload (artist_name from the catalog
    context), NOT from the Playmaker account profile, to prevent account-name vs.
    credited-artist mismatches.

    When ROYALTY_DOCTOR_MOCK_MODE=true (default), returns a canned scored assessment
    without calling the Anthropic API. Set ROYALTY_DOCTOR_MOCK_MODE=false with a valid
    ANTHROPIC_API_KEY to run a live assessment.
    """
    if ROYALTY_DOCTOR_MOCK_MODE:
        result = dict(_ROYALTY_DOCTOR_MOCK_ASSESSMENT)
        result["artist_name"] = req.artist_name
        result["catalog"]     = req.catalog.model_dump()
        # shallow-copy the assessment block so per-request fields don't mutate the template
        assessment = dict(result["assessment"])
        assessment["catalog_name"] = req.catalog.catalog_name
        result["assessment"] = assessment
        return result

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="AI unavailable: ANTHROPIC_API_KEY not configured. "
                                   "Set ROYALTY_DOCTOR_MOCK_MODE=true to use mock mode.")

    system_prompt = build_royalty_doctor_system_prompt(skills_dir=SKILLS_DIR)

    cat = req.catalog

    user_prompt = f"""You are performing a PLMKR Royalty Recovery Audit. You IDENTIFY, DOCUMENT, and QUANTIFY-WHERE-EVIDENCE-SUPPORTS where income is uncollected or underpaid. You rule out normal pipeline lag before claiming any loss, you never fabricate a recoverable figure, and you never render a legal opinion. Use the seven-dimension Royalty Recovery Readiness Rubric, the four hard gates, the Pipeline-First Diagnosis, and the Royalty Recovery Audit template from your knowledge base.

ARTIST IDENTITY (use this — not any account name):
- Credited artist name: {req.artist_name}
- Artist territory: {req.artist_territory}

CATALOG UNDER REVIEW (structured presence/absence flags — full statements/portal exports are NOT supplied unless the data-availability flags say so):
- Catalog name: {cat.catalog_name or 'NOT NAMED'}
- Work count: {cat.work_count}
- Has international usage: {'YES' if cat.has_international_usage else 'NO'}
- Statement data available: {'YES' if cat.statement_data_available else 'NO'}
- Registration export available: {'YES' if cat.registration_export_available else 'NO'}
- PRO registration complete: {'YES' if cat.pro_registration_complete else 'NO'}
- Mechanical registration complete: {'YES' if cat.mechanical_registration_complete else 'NO'}
- Neighboring rights registered: {'YES' if cat.neighboring_rights_registered else 'NO'}
- Identifiers complete (ISWC/ISRC/IPI): {'YES' if cat.identifiers_complete else 'NO'}
- Active revenue without identifiers: {'YES' if cat.active_revenue_without_identifiers else 'NO'}
- Statements verified against DSP data: {'YES' if cat.statements_verified_against_dsp else 'NO'}
- Anomaly review practiced: {'YES' if cat.anomaly_review_practiced else 'NO'}
- Reserve/deductions reviewed: {'YES' if cat.reserve_deductions_reviewed else 'NO'}
- Unmatched-pool claims filed: {cat.unmatched_pool_claims_filed if cat.unmatched_pool_claims_filed is not None else 'NOT STATED'}
- Black-box claim program active: {'YES' if cat.black_box_program_active else 'NO'}
- Proof of ownership ready: {'YES' if cat.proof_of_ownership_ready else 'NO'}
- Active income streams: {', '.join(cat.active_income_streams) if cat.active_income_streams else 'None reported'}
- Audit window status: {cat.audit_window_status}
- Statement history retained: {'YES' if cat.statement_history_retained else 'NO'}
- Soft-audit practice in place: {'YES' if cat.soft_audit_practice else 'NO'}
- Lag-vs-missing tracked: {'YES' if cat.lag_vs_missing_tracked else 'NO'}
- Chain of title documented: {'YES' if cat.chain_of_title_documented else 'NO'}
- Split sheets executed: {'YES' if cat.split_sheets_executed else 'NO'}

ADDITIONAL CONTEXT:
{req.additional_notes or 'None provided.'}

INSTRUCTIONS:
1. Use ONLY the artist name from the ARTIST IDENTITY above.
2. Score all 7 rubric dimensions. For each: letter grade, numeric equivalent, weight, sub-signal classification (MEASURED/SOURCED/JUDGED/AMBIGUOUS/ABSENT/NOT EVALUABLE), confidence (HIGH/MEDIUM/LOW/PARTIAL with reason), and a 1–3 sentence rationale describing the recovery consequence of the current state.
3. State all four hard gates: HG-1 No statement/registration data (NOT EVALUABLE if both data flags are NO), HG-2 Fabricated recovery figure, HG-3 Lag misdiagnosed as underpayment, HG-4 Expired audit window (TIME-CRITICAL if the window is expired). CLEAR or TRIGGERED with reason. If HG-1 triggers, STOP and return NOT EVALUABLE naming the minimum data required.
4. Compute the PROVISIONAL COMPOSITE per the rubric formula. Label it PROVISIONAL and state the unlock condition. Treat any retention/threshold figure as industry convention, not a recommendation.
5. Classify recovery posture descriptively (FULLY_COLLECTING / MINOR_LEAKAGE / NOTABLE_LEAKAGE / SIGNIFICANT_LEAKAGE / SEVERE_LEAKAGE). This labels leakage severity — it is NOT a recommendation to sign, sell, or litigate.
6. Produce a Leak Map (where money is most likely going missing, ranked, each with its evidence basis) and a four-tier Recovery Plan (IMMEDIATE / PRIORITY / OPTIMIZE / MAINTAIN), with recoverable amounts labeled ESTIMATE (with basis) ONLY where evidence supports them, otherwise NOT ESTIMABLE.
7. Apply the Pipeline-First Diagnosis: classify any questioned stream IN TRANSIT / STUCK / UNDERPAID before asserting a loss.
8. Mark NOT EVALUABLE items and name the minimum data required.
9. Do not state any rate, mechanical rate, society retention, or multiple as "market standard" without a Tier A/B source.
10. End with the advisory footer: "{_ROYALTY_DOCTOR_ADVISORY_FOOTER}"
"""

    try:
        resp = await async_client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        assessment_text = resp.content[0].text
    except Exception as e:
        raise HTTPException(status_code=503,
                            detail=f"Royalty recovery assessment failed: {str(e)}")

    return {
        "status":          "ok",
        "mock":            False,
        "artist_name":     req.artist_name,
        "catalog":         req.catalog.model_dump(),
        "assessment_text": assessment_text,
        "advisory_footer": _ROYALTY_DOCTOR_ADVISORY_FOOTER,
        "model":           MODEL_SONNET,
    }
