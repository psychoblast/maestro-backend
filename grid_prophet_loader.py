"""
PLMKR Grid Prophet — context loader.

Reads the knowledge MANIFEST.json and assembles the full marketing system prompt
for the /api/agents/grid-prophet/assess route. Separate from the general
load_knowledge() path so it doesn't affect other agents.
"""
import json
from pathlib import Path

_BASE = Path(__file__).parent


def load_grid_prophet_knowledge(skills_dir: Path | None = None) -> str:
    """
    Load all Grid-Prophet knowledge files in manifest order and return as a
    single concatenated string. Files are joined with section headers so
    the model can orient itself within the knowledge base.
    """
    if skills_dir is None:
        skills_dir = _BASE / "skills"

    manifest_path = skills_dir / "maestro-grid-prophet" / "knowledge" / "MANIFEST.json"
    if not manifest_path.exists():
        return ""

    manifest = json.loads(manifest_path.read_text())
    load_order = manifest.get("load_order", [])
    files_by_id = {f["id"]: f for f in manifest.get("files", [])}

    # Manifest paths are relative to the maestro root (skills_dir's parent)
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


def build_grid_prophet_system_prompt(
    skills_dir: Path | None = None,
    skill_text: str | None = None,
) -> str:
    """
    Assemble the complete system prompt for the Grid-Prophet assessment route.

    - ``skill_text``: pre-loaded SKILL.md content (or None to load from disk)
    - Returns a single string ready to pass as the Anthropic system param
    """
    if skills_dir is None:
        skills_dir = _BASE / "skills"

    if skill_text is None:
        skill_path = skills_dir / "maestro-grid-prophet" / "SKILL.md"
        skill_text = skill_path.read_text() if skill_path.exists() else ""

    knowledge = load_grid_prophet_knowledge(skills_dir=skills_dir)

    parts: list[str] = [skill_text.strip()]
    if knowledge:
        parts.append("---\n# PLMKR MARKETING KNOWLEDGE BASE\n\n" + knowledge)

    return "\n\n".join(parts)
