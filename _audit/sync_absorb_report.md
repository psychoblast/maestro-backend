# Sync absorb-check — read-first report (Unit 3, no code changed)

**Agent under review:** Sync (`sync-agent`) — Sync Licensing, "TV, film, ad sync placements"
**Candidate absorber:** Reed (`ink-and-air`) — Music Publisher, via its `sync_pack` doc-scaffold
**Branch:** `fix/consult-honesty-sweep` (this unit made NO code changes — report only)
**Base:** `origin/main` tip `c5d400a`, unmoved
**Verified directly against current code** — `main.py`, `sync_agent_service.py`,
`ink_and_air_service.py` — not against any stale audit snapshot.

Historical context (not additional undone work): a remote branch
`feat/wire-sync-agent` already exists and is already merged into `origin/main` — that's where
Sync's current 3 tools came from. Confirmed via `git log --all --oneline -- sync_agent_service.py`
style provenance; no action needed on that branch.

---

## What Sync actually is

`SYNC_AGENT_TOOLS` (`main.py:4786`) has exactly 3 tools, backed by `sync_agent_service.py`
(fully in-memory / mock-first — no DB, unlike Sage's `release_service.py`):

- `search_sync_briefs` — searches a curated in-memory library of **open sync-opportunity
  briefs** a music supervisor has posted (TV drama, film trailer, national ad, lifestyle ad,
  AAA game, reality TV), each carrying medium, target genres, a tempo window, an instrumental
  requirement, and a fee range. This is **opportunity discovery** — nothing resembling it exists
  anywhere in `ink_and_air_service.py`.
- `assess_track_sync_fit` — scores a specific track against a **chosen brief's** creative/
  technical requirements (genre match 40pts, tempo-window match 35pts, instrumental-requirement
  match 25pts out of 100), returning matched/missing criteria and a proceed/adjust/blocked
  recommendation. This is **brief-fit matching** — also absent from ink-and-air.
- `submit_sync_pitch` — gated on `SYNC_AGENT_CATALOGUE_CONNECTED`
  (`sync_agent_service._sync_catalogue_connected`, `SyncCatalogueNotConnected` /
  `SyncCatalogueAuthExpired`), and its only effect on success is a `hashlib.sha1`-derived mock
  reference string (`"SYNC-" + digest[:10].upper()`) — this is an **outreach-shaped** action
  (pitch a track to a supervisor on a specific brief), matching the exact Unit-1 retirement
  shape (fake reference, zero real effect, gated).

## What Reed's `sync_pack` scaffold actually is

`build_publishing_doc_scaffold(doc_type="sync_pack", inputs=...)` →
`_scaffold_sync_pack(inputs)` (`ink_and_air_service.py:471-533`) is a pure DATA/SCAFFOLD tool
(Jade-U4 pattern — no model call, no prose, no I/O, imports no anthropic). It assembles a
**sync-licensing metadata document** from `publishing_data.SYNC_METADATA_SPEC`:

- Field-group sections (`SYNC_PACK_FIELD_GROUPS`) — each field is the artist's supplied input
  verbatim, or an explicit `[NEEDS:<field>]` gap; nothing is ever fabricated.
- A "one-stop" status section that asserts `one_stop` ONLY when all three explicit confirmations
  (master control, 100% publishing control, no uncleared samples) are `True` — a directly
  supplied `one_stop_status` is deliberately **disregarded** with a note
  (`HONESTY_RULES.one_stop_explicit_confirmation_only`), never trusted at face value.
- The result carries `_NOT_SUBMIT_READY_NOTE` — it is explicitly a scaffold to review and
  complete, not a submission.

This tool answers "what does the licensing metadata for this track/song need to look like"
— it has **no concept of an open brief, no supervisor, no medium/genre/tempo matching, and no
pitch/submission action of any kind.** It never searches for opportunities and never contacts
anyone; it only formats what the artist already knows about their own rights/ownership
into a document.

## Does Reed fully cover Sync's duties? No.

The three duties are functionally disjoint:

| Sync duty | Shape | Reed's `sync_pack` equivalent |
|---|---|---|
| `search_sync_briefs` | opportunity discovery (read a market of open briefs) | **none** — no brief data, no medium/genre catalogue |
| `assess_track_sync_fit` | fit-scoring against a specific brief's creative/technical spec | **none** — no scoring, no brief object to score against |
| `submit_sync_pitch` | outreach (pitch a track to a supervisor on a brief) | **none** — `sync_pack` never contacts anyone; it is a document, not an action |

Reed's `sync_pack` is DOCUMENT-WRITER-shaped (assemble a metadata pack once a deal or pitch is
already in motion); Sync's three tools are OUTREACH-shaped (find the opportunity, judge the fit,
pitch it). These sit on opposite sides of the same workflow — a sync pack is typically what you
send *after* a supervisor has expressed interest from a pitch, not a substitute for finding and
pitching the opportunity in the first place. There is no tool-name, data-structure, or function
overlap between the two services to fold.

## Conclusion

**Sync has genuinely distinct duties that Reed's doc-scaffold does not perform.** This is not a
clean fold — per the unit's decision tree, no code was changed. `submit_sync_pitch` remains
exactly as it was (a Unit-1-shaped mock/gated tool), but retiring it was explicitly out of scope
for this unit: Unit 3's mandate was "retire Sync's tools only if Reed's coverage is a clean
substitute," and it is not. (Whether `submit_sync_pitch` should separately be considered for a
future Unit-1-style mock-retirement pass — on its own merits, independent of any fold-into-Reed
question — is a decision for Tommy; flagging it here for visibility since its shape is identical
to the 14 tools retired in this branch's `[SWEEP]` commit, but Sync was explicitly excluded from
that sweep by name and this unit's scope is the absorb question only, not a general retirement
mandate.)

Full suite re-run to confirm the branch is unaffected (0 code changes ⇒ 0 risk) — see final
report for the shared post-Unit-3 suite run.

**SYNC_ABSORB_DISTINCT_DUTIES_RETAINED**
