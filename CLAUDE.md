# Maestro — AI Artist Management Platform

## What This Is
Maestro is a global AI artist management platform with 38 specialist agents. The brain is already built and running via OpenClaw. We are now building the voice interface and web portal on top of it.

## Existing Infrastructure
- OpenClaw gateway: running as systemd service
- 38 agent SKILL.md files: ~/.openclaw/workspace/skills/
- Artist data store: ~/.openclaw/workspace/maestro/data/artist_store.json
- Knowledge base: ~/.openclaw/workspace/KNOWLEDGE.md
- Claude API: already configured in OpenClaw

## What We Are Building — Phase 2: Voice
A web interface where artists can:
1. See all 38 agents as real people with names and photos
2. Click any agent to start a voice call
3. Speak — Whisper transcribes their voice to text
4. Text goes to Claude API with the correct agent SKILL.md as system prompt
5. Response comes back as text
6. Kokoro TTS speaks the response in that agent's unique voice
7. Artist hears the agent respond like a real person

## Agent Names
- PUPPET-MASTER → Marcus (Artist Manager)
- LEX-CIPHER → Lex (Entertainment Lawyer)
- FUND-PHANTOM → Jade (Grants & Funding)
- RIGHTS-PULSE → Ray (Performance Rights)
- BORDER-ROYALTY → Cleo (Neighbouring Rights)
- MECH-LEDGER → Finn (Mechanical Royalties)
- VAULT-KEEPER → Victor (Business Manager)
- LEDGER-LOCK → Nadia (Accountant)
- SIGNAL-BLASTER → Zara (Publicist)
- GRID-PROPHET → Kai (Digital Marketing)
- VISION-FORGE → Luna (AI Visuals)
- DESIGN-STUDIO → Diego (Brand Designer)
- VENUE-HAWK → Ray B (Booking Agent)
- TOUR-COMMANDER → Miles (Tour Manager)
- AIRWAVE → Solo (Radio & Playlist)
- BRAND-CONNECT → Nia (Brand Partnerships)
- MERCH-EMPIRE → Max (Merchandise)
- FAN-BUILDER → Aria (Fan Engagement)
- SYNC-AGENT → Sync (Sync Licensing)
- GLOBAL-SCOUT → Nova (International)
- CREATIVE-DIRECTOR → Cree (Creative Director)
- DATA-ORACLE → Data (Analytics)
- AR-SCOUT → Scout (A&R)
- PRODUCER-CONNECT → Beat (Production)
- MUSIC-EDU → Prof (Education)
- COLLAB-CONNECT → Collab (Networking)
- ARTIST-WELLNESS → Maya (Wellness)
- PRESS-MONITOR → Press (Media Monitor)
- LIVE-COACH → Coach (Performance)
- AUDIO-QUALITY → Audio (Quality Control)
- AI-NAVIGATOR → Neo (AI Tools)
- ROYALTY-DOCTOR → Doc (Royalty Recovery)
- VIDEO-DIRECTOR → Reel (Music Video)
- MOBILE-MONETIZE → Mo (Monetization)
- STOREFRONT → Store (Fan Store)
- CONTENT-FORGE → Pen (Content Creation)
- SCHEDULE-KEEPER → Cal (Scheduling)
- COLLAB-CONNECT → Link (Collaboration)

## Tech Stack
- Backend: FastAPI (Python)
- Voice input: Whisper (already installed via pip)
- Voice output: Kokoro TTS (open source, install via pip)
- Frontend: HTML/CSS/JS — production grade, dark aesthetic
- Agent brains: Claude API (claude-sonnet-4-20250514)
- Data: existing artist_store.json

## Design Direction
- Dark, premium aesthetic — think high-end music industry
- Each agent has a profile card with photo placeholder, name, title, specialty
- Clean dashboard — artist sees their whole team at a glance
- Click to call — simple, intuitive
- Voice visualizer when agent is speaking
- Mobile responsive

## GSD Rules
- Build it, don't just plan it
- Working code over perfect code
- Test as you go
- No placeholders — real functionality only
