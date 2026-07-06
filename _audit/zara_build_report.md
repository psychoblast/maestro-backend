# Zara — publicity/press OUTREACH build report (feat/zara-press-outreach)

Branch off `1bca48f`. Two units, committed + pushed after each. Full suite green.
No STEP-0 collision phase for Zara (not required by the run prompt — Ray B's was the
only agent with a step-0 collision investigation this run).

## U1 — publicity_data.py (commit ZARA-U1, `5454554`)
Data-only corpus (`ZARA_PUBLICITY_MAP_v1`). Constants: `PITCH_MECHANISM_TYPES`,
`EMBARGO_DOCTRINE`, `LEAD_TIME_DOCTRINE`, `LIST_AND_PERSONALIZATION_DOCTRINE`,
`PITCH_PACKAGE_SPEC`, `INTEGRITY_DOCTRINE`, `OUT_OF_SCOPE`, `HONESTY_RULES`. Same
conventions as grant_data/brand_partnerships_data/booking_data: pure literals (AST:
no def/class/import/call), JSON-serializable, `None`+verify-live for unknowns, free
text = note never rule. **ZERO currency.** No fabricated outlet/journalist/coverage
patterns — media targets are `[ARTIST-SUPPLIED:media_list]` or
`[NEEDS:media_targets]` only. Boundaries (creative-director / puppet-master /
airwave / brand-connect) present. 16 proof tests.

## U2 — tools + dispatch (commit ZARA-U2, `c9473db`)
`signal_blaster_service.py` reworked to the Marcus/Nia/Solo OUTREACH pattern;
`main.py` `SIGNAL_BLASTER_TOOLS` + `_execute_signal_blaster_tool` rewired.

| Tool | Class | Behaviour |
|---|---|---|
| `search_media_outlets` | CONSULT | Filters an ARTIST-SUPPLIED `media_list` on beat/level. No built-in directory — no list → `[NEEDS:media_targets]`; list → `[ARTIST-SUPPLIED:media_list]`. Never fabricates an outlet or journalist name. |
| `build_pitch_plan` | CONSULT (Option B) | Compact ingredients only: recommended pitch mode (from `PITCH_MECHANISM_TYPES.selection_doctrine`, never invented) + a lead-ordered timeline off `LEAD_TIME_DOCTRINE` anchored to a supplied release date + a package checklist with aggregated `missing[]`. Short `weeks_to_release` marks slots `compressed` and returns an honest `compression_warning` — never a silently shortened schedule. Press release only ever *referenced* (creative-director's `build_copy_scaffold`), never drafted here. Agent writes the prose. |
| `lookup_publicity_doctrine` | CONSULT | Pure read over publicity_data.py (7 topics) + full honesty-rule set. Ungated. |
| `send_press_pitch` | MOCK (gated) | Gate `PRESS_OUTREACH_CONNECTED`; `PPITCH-`+sha1 via the in-repo `_submit_press_pitch` seam; model writes subject/body (ride out verbatim); zero LLM in the tool layer. `pitch_mode` explicit (standard/embargo/exclusive); embargo without a zoned `embargo_lift_datetime` is HELD with `[NEEDS:embargo_lift_datetime]`, never guessed. |

**Removed:** nothing pre-existing needed removal — Zara had no cross-agent
duplicate tools (unlike Ray B/live-wire). The prior `test_wire_signal_blaster.py`
(5 tests, pre-rework) was reworked in place to the new 8-test roster; net +3 in
that file.

Press-release/bio/EPK drafting requests are handled purely as doctrine: both the
`lookup_publicity_doctrine` tool description and the `build_pitch_plan` /
`send_press_pitch` docstrings route the model to creative-director's
`build_copy_scaffold` (Cree writes, Zara sends) — no cross-service dispatch call
was added.

## Self-check
- [x] publicity_data.py purity + serializable + ZERO currency + no fabricated-outlet
      patterns (16 tests).
- [x] search_media_outlets never fabricates (needs_targets / artist_supplied paths
      tested).
- [x] build_pitch_plan: mode recommendation off selection doctrine, timeline
      compression warning (honest, not silent), package `missing[]` aggregation.
- [x] send_press_pitch: gated (connected/not-connected/expired) + deterministic
      PPITCH- sha1 + verbatim subject/body + missing_outlet path + embargo-without-lift
      HELD path (service sanity + wire, tests a–f).
- [x] No-prose send seam: tool never generates body; AST test proves no `anthropic`
      import and no `*.messages.create` in signal_blaster_service (test h).
- [x] lookup_publicity_doctrine: ok / unknown_topic paths.
- [x] Roster: newest unit owns exact SIGNAL_BLASTER_TOOLS roster (4 tools, drafting
      tool absent) (test g).
- [x] Gate exclusivity: Marcus still uses MARCUS_TOOLS, non-signal agent (music-edu)
      never receives SIGNAL_BLASTER_TOOLS (tests b, c).
- [x] Entity gate PASS on staged U2 diff (`tests/entity_wall_terms.py`, zero hits).
- [x] Full suite **2863 passed**, 0 failures (floor 2844 → 2863: +16 publicity_data,
      +3 net in test_wire_signal_blaster.py), run chunked 25×8 top-level files +
      tests/integration/ (26 chunks), no native crash on any chunk, reconciled
      exactly against `pytest tests/ --collect-only` (2863). Exit 0 on every chunk.
- [x] Commit + push after each unit; no `git add -A` (files staged explicitly);
      no destructive git.

**ZARA COMPLETE.**
