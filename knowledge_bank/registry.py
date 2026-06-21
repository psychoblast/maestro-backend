"""
Knowledge bank registry — the data-driven catalog of expert domains.

Each domain points at an existing ``skills/maestro-<slug>/knowledge`` directory
that ships a ``MANIFEST.json``. ``load_domain`` reads that manifest and assembles
the knowledge text in the manifest's declared ``load_order`` — the SAME assembly
the per-agent loaders use (read one, e.g. ``ar_scout_loader.py``, to confirm).

Adding a domain later is a ONE-LINE addition to ``_DOMAINS`` below.

This module performs NO LLM/API calls. It only reads files already in the repo.
"""
import json
from pathlib import Path
from typing import NamedTuple

# Repo root: knowledge_bank/ lives directly under it.
_BASE = Path(__file__).resolve().parent.parent
_SKILLS_DIR = _BASE / "skills"


class Domain(NamedTuple):
    """One expert domain in the bank."""
    key: str           # stable domain key used by the brain / callers
    slug: str          # skills/maestro-<slug>/knowledge source directory
    display_name: str  # human-readable label for sectioning
    source_dir: Path | None = None  # explicit knowledge dir; default = skills/maestro-<slug>/knowledge


# ── The domain catalog ──────────────────────────────────────────────────────────
# slug -> domain map is fixed by the re-homed expert knowledge already in the repo.
# To add a domain later, append ONE Domain(...) line here.
_DOMAINS: tuple[Domain, ...] = (
    Domain("ar",                "ar-scout",         "A&R Scouting"),
    Domain("marketing",         "grid-prophet",     "Marketing & Growth"),
    Domain("sync",              "sync-agent",       "Sync Licensing"),
    Domain("bizdev",            "brand-connect",    "Brand & Business Development"),
    Domain("legal",             "lex-cipher",       "Legal & Contracts"),
    Domain("live_touring",      "tour-commander",   "Live & Touring"),
    Domain("publishing",        "ink-and-air",      "Publishing"),
    Domain("finance_royalties", "royalty-doctor",   "Finance & Royalties"),
    Domain("production",        "producer-connect", "Production"),
    Domain("capital_funding",   "capital-funding",  "Capital and funding", _BASE / "knowledge_bank" / "domains" / "capital_funding"),
    Domain("controller",        "controller",       "Financial controller", _BASE / "knowledge_bank" / "domains" / "controller"),
    Domain("data_analytics",    "data-analytics",   "Data and analytics", _BASE / "knowledge_bank" / "domains" / "data_analytics"),
    Domain("digital_ops",       "digital-ops",      "Digital operations", _BASE / "knowledge_bank" / "domains" / "digital_ops"),
    Domain("executive",         "executive",        "Executive strategy", _BASE / "knowledge_bank" / "domains" / "executive"),
    Domain("fan_social",        "fan-social",       "Fan and social", _BASE / "knowledge_bank" / "domains" / "fan_social"),
    Domain("intelligence",      "intelligence",     "Market intelligence", _BASE / "knowledge_bank" / "domains" / "intelligence"),
    Domain("label_ops",         "label-ops",        "Label operations", _BASE / "knowledge_bank" / "domains" / "label_ops"),
    Domain("management",        "management",       "Artist management", _BASE / "knowledge_bank" / "domains" / "management"),
)

_DOMAINS_BY_KEY: dict[str, Domain] = {d.key: d for d in _DOMAINS}


def list_domains() -> list[str]:
    """Return the registered domain keys in catalog order."""
    return [d.key for d in _DOMAINS]


def get_domain(key: str) -> Domain:
    """Return the Domain record for ``key`` or raise a clear KeyError."""
    try:
        return _DOMAINS_BY_KEY[key]
    except KeyError:
        raise KeyError(
            f"Unknown knowledge-bank domain: {key!r}. "
            f"Known domains: {', '.join(list_domains())}"
        )


def _source_dir(domain: Domain, skills_dir: Path) -> Path:
    """Absolute path to a domain's knowledge directory.

    Honors an explicit ``source_dir`` override (used by domains whose knowledge
    lives under ``knowledge_bank/domains/<key>`` rather than ``skills/``); falls
    back to the ``skills/maestro-<slug>/knowledge`` convention otherwise.
    """
    if domain.source_dir is not None:
        return domain.source_dir
    return skills_dir / f"maestro-{domain.slug}" / "knowledge"


def load_domain(key: str, skills_dir: Path | None = None) -> str:
    """
    Assemble and return the knowledge text for a single domain.

    Reads the domain's ``MANIFEST.json`` and concatenates each file in the
    manifest's ``load_order``, joined with ``\\n\\n---\\n\\n`` section separators
    — identical to the per-agent loaders. An unknown ``key`` raises KeyError; a
    missing manifest raises FileNotFoundError (the 9 catalog domains all ship one).
    """
    if skills_dir is None:
        skills_dir = _SKILLS_DIR

    domain = get_domain(key)
    knowledge_dir = _source_dir(domain, skills_dir)
    manifest_path = knowledge_dir / "MANIFEST.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Knowledge manifest missing for domain {key!r}: {manifest_path}"
        )

    manifest = json.loads(manifest_path.read_text())
    load_order = manifest.get("load_order", [])
    files_by_id = {f["id"]: f for f in manifest.get("files", [])}

    # Manifest paths are relative to the maestro root (skills_dir's parent).
    maestro_root = skills_dir.parent

    sections: list[str] = []
    for file_id in load_order:
        meta = files_by_id.get(file_id)
        if not meta:
            continue
        file_path = maestro_root / meta["path"]
        if not file_path.exists():
            continue
        content = file_path.read_text().strip()
        if content:
            sections.append(content)

    return "\n\n---\n\n".join(sections)
