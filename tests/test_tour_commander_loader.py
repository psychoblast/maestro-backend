"""
Tests for tour_commander_loader — context loader for the tour assessment route.

All tests are mocked/in-process. No network calls.
"""
import json
import importlib
from pathlib import Path

import pytest

from entity_wall_terms import assert_no_forbidden_terms


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_knowledge_tree(tmp_path: Path) -> Path:
    """Create a minimal fake skills dir with a manifest and two knowledge files."""
    skills_dir = tmp_path / "skills"
    knowledge_dir = skills_dir / "maestro-tour-commander" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "tour-doctrine", "path": "skills/maestro-tour-commander/knowledge/doctrine.md",
             "role": "core-doctrine", "required": True, "description": "test doctrine"},
            {"id": "campaign-quality-rubric", "path": "skills/maestro-tour-commander/knowledge/rubric.md",
             "role": "scoring-rubric", "required": True, "description": "test rubric"},
        ],
        "load_order": ["tour-doctrine", "campaign-quality-rubric"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "doctrine.md").write_text("# Tour Doctrine\nModel first, route second.")
    (knowledge_dir / "rubric.md").write_text("# Campaign Quality Rubric\nEight dimensions.")

    skill_dir = skills_dir / "maestro-tour-commander"
    (skill_dir / "SKILL.md").write_text("# TOUR-COMMANDER SKILL\nYou are Miles.")

    return skills_dir


# ── load_tour_commander_knowledge ───────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    result = tour_commander_loader.load_tour_commander_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = tour_commander_loader.load_tour_commander_knowledge(skills_dir=skills_dir)

    assert "# Tour Doctrine" in result
    assert "# Campaign Quality Rubric" in result
    # Doctrine appears before rubric (load order preserved)
    assert result.index("# Tour Doctrine") < result.index("# Campaign Quality Rubric")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-tour-commander" / "knowledge" / "rubric.md").unlink()

    result = tour_commander_loader.load_tour_commander_knowledge(skills_dir=skills_dir)
    assert "# Tour Doctrine" in result
    assert "# Campaign Quality Rubric" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-tour-commander" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = tour_commander_loader.load_tour_commander_knowledge(skills_dir=skills_dir)
    assert "# Tour Doctrine" in result


# ── build_tour_commander_system_prompt ──────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = tour_commander_loader.build_tour_commander_system_prompt(skills_dir=skills_dir)
    assert "TOUR-COMMANDER SKILL" in prompt
    assert "PLMKR TOUR & LIVE KNOWLEDGE BASE" in prompt
    assert "# Tour Doctrine" in prompt
    assert "# Campaign Quality Rubric" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = tour_commander_loader.build_tour_commander_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM TOUR SKILL TEXT",
    )
    assert "CUSTOM TOUR SKILL TEXT" in prompt
    assert "PLMKR TOUR & LIVE KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = tour_commander_loader.build_tour_commander_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY TOUR SKILL TEXT",
    )
    assert "ONLY TOUR SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import tour_commander_loader
    importlib.reload(tour_commander_loader)

    prompt = tour_commander_loader.build_tour_commander_system_prompt()

    assert_no_forbidden_terms(prompt)
