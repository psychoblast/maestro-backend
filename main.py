import os
import re
import io
import json
import time
import secrets
import base64
import random
import tempfile
import asyncio
import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse as _RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import anthropic
import httpx

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Base directory: defaults to the folder containing this file so both local
# and Docker deployments work without explicit env overrides.
_BASE = Path(__file__).parent

SKILLS_DIR    = Path(os.environ.get("SKILLS_DIR",     _BASE / "skills"))
ARTISTS_DIR   = Path(os.environ.get("ARTISTS_DIR",    _BASE / "data/artists"))
KNOWLEDGE_BASE= Path(os.environ.get("KNOWLEDGE_BASE", _BASE / "KNOWLEDGE.md"))
AUDIO_CACHE   = Path(os.environ.get("AUDIO_CACHE_DIR",_BASE / "audio_cache"))
AUDIO_CACHE.mkdir(parents=True, exist_ok=True)

# Cloud integrations (optional — graceful degradation when absent)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
ELEVENLABS_API_KEY    = os.environ.get("ELEVENLABS_API_KEY", "")

# Sync client for non-streaming endpoints, async client for streaming
client       = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

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
    print(f"[SKILLS] Pre-loaded {loaded} skill files ({missing} missing)")

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
   "I'll hand you over to [FIRST NAME], our [TITLE]. When you're ready, click the button below to be connected."
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
    # Primary canonical trigger — matches new button-handoff wording
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
        try:
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro(
                str(_BASE / "kokoro-v1.0.onnx"),
                str(_BASE / "voices-v1.0.bin")
            )
            _kokoro_available = True
            print("[TTS] Kokoro loaded OK")
        except Exception as e:
            print(f"[TTS] Kokoro unavailable: {e}")
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
            print(f"[TTS] error: {e}")
            return None

# ── ElevenLabs TTS (cloud fallback) ────────────────────────────────────────────
# Maps Kokoro voice prefix → ElevenLabs pre-made voice ID
_RACHEL = "21m00Tcm4TlvDq8ikWAM"
_BELLA  = "EXAVITQu4vr4xnSDxMaL"
_ADAM   = "pNInz6obpgDQGcFmaJgB"

# ── Per-agent distinct ElevenLabs voice IDs — 16 active agents ────────────────
# Each voice is chosen to match the agent's character: gender, age, accent, personality.
# No two active agents share a voice ID.
_EL_VOICE_MAP = {
    "am_onyx":    "pNInz6obpgDQGcFmaJgB",  # Marcus — Adam   (authoritative American male)
    "af_jessica": "21m00Tcm4TlvDq8ikWAM",  # Lex    — Rachel (clear, professional female)
    "af_heart":   "LcfcDJNUP1GQjkzn1xUU",  # Jade   — Emily  (warm, encouraging female)
    "am_echo":    "VR6AewLTigWG4xSOukaG",  # Ray    — Arnold (firm, knowledgeable male)
    "bf_emma":    "ThT5KcBeYPX3keUQqHPh",  # Nadia  — Dorothy (precise British female)
    "am_michael": "TX3LPaxmHKxFdv7VOFE",  # Mo     — Liam   (energetic young male)
    "bm_george":  "IKne3meq5aSn9XLyUdCD",  # Tommy  — Charlie (distinct British/Aus male)
    "af_bella":   "AZnzlk1XvdvUeBnXmlld",  # Zara   — Domi   (strong, energetic female)
    "am_adam":    "ErXwobaYiN019PkySvjV",  # Kai    — Antoni (tech-savvy young male)
    "am_liam":    "TxGEqnHWrfWFTfGW9XjX",  # Solo   — Josh   (smooth, charismatic male)
    "am_fenrir":  "yoZ06aMxZJJ28mfd3POQ",  # Ray B  — Sam    (raspy, street-smart male)
    "bm_lewis":   "GBv7mTt0atIp3Br8iCZE",  # Miles  — Thomas (calm, organized male)
    "af_river":   "MF3mGyEYCl7XYWbV9V6O",  # Cree   — Elli   (creative, expressive female)
    "bf_isabella":"EXAVITQu4vr4xnSDxMaL",  # Sync   — Bella  (sophisticated British female)
    "af_kore":    "piTKgcLEGmPE4e6mEKli",  # Scout  — Nicole (perceptive, nuanced female)
    "af_sarah":   "oWAxZDx7w5VEj9dCyTzz",  # Cal    — Grace  (warm, organized female)
}

_EL_VOICES = {
    # Prefix fallback for non-active agents
    "af": _RACHEL,  # American female
    "bf": _BELLA,   # British female
    "ef": _BELLA,   # European female
    "ff": _BELLA,   # French female
    "hf": _RACHEL,  # Hindi female
    "if": _BELLA,   # Italian female
    "jf": _RACHEL,  # Japanese female
    "pf": _BELLA,   # Polish female
    "zf": _RACHEL,  # Chinese female
    "am": _ADAM,    # American male
    "bm": _ADAM,    # British male
    "em": _ADAM,    # European male
    "hm": _ADAM,    # Hindi male
    "im": _ADAM,    # Italian male
    "jm": _ADAM,    # Japanese male
    "pm": _ADAM,    # Polish male
    "zm": _ADAM,    # Chinese male
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
            print(f"[TTS] ElevenLabs HTTP {r.status_code} | voice_id={voice_id} | key_prefix={ELEVENLABS_API_KEY[:8]}...")
            if r.status_code != 200:
                _tts_last_error["detail"] = f"HTTP {r.status_code}: {r.text[:500]}"
                print(f"[TTS] ElevenLabs error body: {r.text[:500]}")
            r.raise_for_status()
        wav = _pcm_to_wav(r.content, sr=24000)
        cache_file.write_bytes(wav)
        _tts_last_error["detail"] = None
        print(f"[TTS] ElevenLabs OK: {len(wav)} bytes")
        return wav
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        _tts_last_error.setdefault("detail", msg)
        print(f"[TTS] ElevenLabs exception: {msg}")
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
    path = ARTISTS_DIR / f"{artist_id}.json"
    return json.loads(path.read_text()) if path.exists() else {}

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
        print("\u26a0️  TWILIO_ACCOUNT_SID not set \u2014 SMS OTP disabled")
        ok = False
    if not re.fullmatch(r'[0-9a-f]{32}', token):
        print(f"\u26a0️  TWILIO_AUTH_TOKEN invalid (got {len(token)} chars, need exactly 32 lowercase hex chars)")
        print("    \u27a4  Get it from: console.twilio.com \u2192 Account \u2192 General Settings \u2192 Auth Token")
        print("    \u27a4  Format: 32 chars, only 0-9 and a-f, e.g. a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4")
        print("    \u27a4  Update ~/.bashrc then: source ~/.bashrc && restart uvicorn")
        ok = False
    if not phone:
        print("\u26a0️  TWILIO_PHONE_NUMBER not set \u2014 SMS OTP disabled")
        ok = False
    if ok:
        print("\u2713  Twilio env vars look valid")
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        print("\u26a0️  STRIPE_SECRET_KEY not set \u2014 billing checkout disabled")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        print("\u26a0️  ANTHROPIC_API_KEY not set \u2014 AI agents will fail!")
    else:
        print("\u2713  ANTHROPIC_API_KEY present")

_check_env()

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Playmaker", version="2.2.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
DB_PATH  = Path(os.environ.get("DB_PATH", _BASE / "memory.db"))
_db_lock = asyncio.Lock()

def _ensure_db():
    """Create messages table + index on first use (idempotent)."""
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
    conn.commit()
    conn.close()
    print("[DB] memory.db ready")

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

# ── Module-level init ──────────────────────────────────────────────────────────
# Run synchronously at import time so the DB and Kokoro are ready before the
# first request arrives (avoids the 20-35s first-call warmup delay).
_ensure_db()
_threading.Thread(target=get_kokoro, daemon=True, name="kokoro-warmup").start()
print("[INIT] DB ready, Kokoro warmup thread started")

@app.get("/api/agents")
async def list_agents():
    return {"agents": AGENTS}

@app.get("/api/artist")
async def get_artist(artist_id: str = ""):
    return load_artist(artist_id)

@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        model = get_whisper()
        # Derive extension from filename so Whisper decodes correctly.
        # Android expo-av records .m4a; iOS .m4a; web .webm — default .m4a.
        filename  = audio.filename or "voice.m4a"
        ext       = os.path.splitext(filename)[1] or ".m4a"
        data      = await audio.read()
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

    # Extract the reason for handoff from the last user message in the history
    last_user_msg = next((t["content"] for t in reversed(trimmed_history) if t.get("role") == "user"), "")
    reason_line = f"They came to {from_name} about: {last_user_msg[:200]}\n" if last_user_msg else ""

    handoff_prompt = (
        f"{from_name} just handed {artist_name} directly to you. You are now their point of contact.\n"
        f"{reason_line}"
        f"Greet {artist_name} by name. Reference exactly what they need. Tell them what you will do for them right now.\n"
        f"Two sentences maximum. Under 60 words. Zero markdown. No filler. Sound like the expert you are."
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

    # For greeting pings, verify history from DB directly — don't trust client-provided
    # history list, which may be empty on first open even if the artist profile exists.
    if message == "__greet__":
        db_count  = await _get_message_count(artist_id, agent_id)
        has_history = db_count > 0
        if not has_history:
            # First-time greeting: return static greeting instantly — zero Claude API call.
            # This cuts greeting latency from 10-14s to ~2s (TTS only).
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
async def health():
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

@app.post("/api/artist/save")
async def save_artist(profile: ArtistProfile):
    try:
        ARTISTS_DIR.mkdir(parents=True, exist_ok=True)
        artist_file = ARTISTS_DIR / f"{profile.artist_id}.json"

        # Load existing profile or start fresh
        existing = {}
        if artist_file.exists():
            try:
                existing = json.loads(artist_file.read_text())
            except Exception:
                existing = {}

        # Map app profile fields to the store format Maestro expects
        existing.update({
            "artist_id":        profile.artist_id,
            "artist_name":      profile.name,
            "country":          profile.country,
            "genres":           profile.genres,
            "monthly_listeners": profile.monthly_listeners,
            "tier":             profile.tier,
            "onboarded":        profile.onboarded,
        })

        artist_file.write_text(json.dumps(existing, indent=2))
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

        ARTISTS_DIR.mkdir(parents=True, exist_ok=True)
        artist_file = ARTISTS_DIR / f"{payload.artist_id}.json"

        existing = {}
        if artist_file.exists():
            try:
                existing = json.loads(artist_file.read_text())
            except Exception:
                existing = {}

        existing["tier"] = payload.tier
        artist_file.write_text(json.dumps(existing, indent=2))
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
    """Find existing artist profile by name (case-insensitive) across all artist files."""
    try:
        if not ARTISTS_DIR.exists():
            return {"found": False}
        target = name.lower().strip()
        for path in ARTISTS_DIR.glob("*.json"):
            try:
                profile = json.loads(path.read_text())
            except Exception:
                continue
            if profile.get("artist_name", "").lower() == target:
                return {
                    "found": True,
                    "artist_id": profile.get("artist_id"),
                    "name": profile.get("artist_name"),
                    "tier": profile.get("tier", "Gold"),
                    "genres": profile.get("genres", []),
                    "country": profile.get("country", ""),
                    "monthly_listeners": profile.get("monthly_listeners", ""),
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

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            raise HTTPException(status_code=503, detail="SMS service not configured — set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")

        otp = str(secrets.randbelow(1000000)).zfill(6)
        _otp_store[phone] = {"otp": otp, "expires": time.time() + OTP_EXPIRY_SECONDS}

        # Validate auth token format — Twilio tokens are exactly 32 lowercase hex chars
        import re as _re
        token_valid = bool(auth_token and len(auth_token) == 32 and _re.fullmatch(r"[0-9a-f]+", auth_token.lower()))

        if not token_valid:
            raise HTTPException(
                status_code=503,
                detail=f"SMS not configured — TWILIO_AUTH_TOKEN must be exactly 32 lowercase hex characters (got {len(auth_token or '')} chars). Set the correct token in Railway env vars."
            )

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


def _load_artist_file(artist_id: str) -> tuple[Path, dict]:
    """Return (path, data) for an artist's JSON file."""
    path = ARTISTS_DIR / f"{artist_id}.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    return path, data


def _save_artist_file(path: Path, data: dict):
    ARTISTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


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

STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_AVAILABLE      = bool(STRIPE_SECRET_KEY)
APP_BASE_URL          = os.environ.get("APP_BASE_URL", "http://192.168.18.59:8765")

if STRIPE_AVAILABLE:
    stripe_lib.api_key = STRIPE_SECRET_KEY

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
        if STRIPE_WEBHOOK_SECRET:
            event = stripe_lib.Webhook.construct_event(body, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = stripe_lib.Event.construct_from(json.loads(body), stripe_lib.api_key)
    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
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
        for f in ARTISTS_DIR.glob("*.json"):
            try:
                adata = json.loads(f.read_text())
                if adata.get("subscription_id") == sub_id:
                    if etype == "customer.subscription.deleted" or status == "canceled":
                        adata["subscription_status"] = "canceled"
                        adata["tier"] = "Gold"
                    else:
                        adata["subscription_status"] = status
                    _save_artist_file(f, adata)
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
