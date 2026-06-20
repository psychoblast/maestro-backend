"""
Tests for ink_and_air_loader — context loader for the publishing assessment route.

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
    knowledge_dir = skills_dir / "maestro-ink-and-air" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "publishing-doctrine", "path": "skills/maestro-ink-and-air/knowledge/doctrine.md",
             "role": "core-doctrine", "required": True, "description": "test doctrine"},
            {"id": "catalog-health-rubric", "path": "skills/maestro-ink-and-air/knowledge/rubric.md",
             "role": "scoring-rubric", "required": True, "description": "test rubric"},
        ],
        "load_order": ["publishing-doctrine", "catalog-health-rubric"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "doctrine.md").write_text("# Publishing Doctrine\nThe unpaid dollar.")
    (knowledge_dir / "rubric.md").write_text("# Catalog Health Rubric\nTen dimensions.")

    skill_dir = skills_dir / "maestro-ink-and-air"
    (skill_dir / "SKILL.md").write_text("# INK-AND-AIR SKILL\nYou are Reed.")

    return skills_dir


# ── load_ink_and_air_knowledge ─────────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    result = ink_and_air_loader.load_ink_and_air_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = ink_and_air_loader.load_ink_and_air_knowledge(skills_dir=skills_dir)

    assert "# Publishing Doctrine" in result
    assert "# Catalog Health Rubric" in result
    # Doctrine appears before rubric (load order preserved)
    assert result.index("# Publishing Doctrine") < result.index("# Catalog Health Rubric")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-ink-and-air" / "knowledge" / "rubric.md").unlink()

    result = ink_and_air_loader.load_ink_and_air_knowledge(skills_dir=skills_dir)
    assert "# Publishing Doctrine" in result
    assert "# Catalog Health Rubric" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-ink-and-air" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = ink_and_air_loader.load_ink_and_air_knowledge(skills_dir=skills_dir)
    assert "# Publishing Doctrine" in result


# ── build_ink_and_air_system_prompt ────────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = ink_and_air_loader.build_ink_and_air_system_prompt(skills_dir=skills_dir)
    assert "INK-AND-AIR SKILL" in prompt
    assert "PLMKR PUBLISHING & RIGHTS KNOWLEDGE BASE" in prompt
    assert "# Publishing Doctrine" in prompt
    assert "# Catalog Health Rubric" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = ink_and_air_loader.build_ink_and_air_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM PUBLISHING SKILL TEXT",
    )
    assert "CUSTOM PUBLISHING SKILL TEXT" in prompt
    assert "PLMKR PUBLISHING & RIGHTS KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = ink_and_air_loader.build_ink_and_air_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY PUBLISHING SKILL TEXT",
    )
    assert "ONLY PUBLISHING SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import ink_and_air_loader
    importlib.reload(ink_and_air_loader)

    prompt = ink_and_air_loader.build_ink_and_air_system_prompt()

    assert_no_forbidden_terms(prompt)
