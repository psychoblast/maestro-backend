"""
Tests for grid_prophet_loader — context loader for marketing deep assessment.

All tests are mocked/in-process. No network calls.
"""
import json
import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent))
from entity_wall_terms import assert_no_forbidden_terms


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_knowledge_tree(tmp_path: Path) -> Path:
    """Create a minimal fake skills dir with a manifest and two knowledge files."""
    skills_dir = tmp_path / "skills"
    knowledge_dir = skills_dir / "maestro-grid-prophet" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "scoring-rubric", "path": "skills/maestro-grid-prophet/knowledge/scoring-rubric.md",
             "role": "core-doctrine", "required": True, "description": "test rubric"},
            {"id": "campaign-arch", "path": "skills/maestro-grid-prophet/knowledge/campaign-arch.md",
             "role": "campaign-method", "required": True, "description": "test campaign arch"},
        ],
        "load_order": ["scoring-rubric", "campaign-arch"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "scoring-rubric.md").write_text("# Rubric Content\n8 dimensions.")
    (knowledge_dir / "campaign-arch.md").write_text("# Campaign Architecture\n12-week arc.")

    skill_dir = skills_dir / "maestro-grid-prophet"
    (skill_dir / "SKILL.md").write_text("# GRID-PROPHET SKILL\nYou are Kai.")

    return skills_dir


# ── load_grid_prophet_knowledge ────────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    result = grid_prophet_loader.load_grid_prophet_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = grid_prophet_loader.load_grid_prophet_knowledge(skills_dir=skills_dir)

    assert "# Rubric Content" in result
    assert "# Campaign Architecture" in result
    assert result.index("# Rubric Content") < result.index("# Campaign Architecture")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-grid-prophet" / "knowledge" / "campaign-arch.md").unlink()

    result = grid_prophet_loader.load_grid_prophet_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result
    assert "# Campaign Architecture" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-grid-prophet" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = grid_prophet_loader.load_grid_prophet_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result


# ── build_grid_prophet_system_prompt ──────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = grid_prophet_loader.build_grid_prophet_system_prompt(skills_dir=skills_dir)
    assert "GRID-PROPHET SKILL" in prompt
    assert "PLMKR MARKETING KNOWLEDGE BASE" in prompt
    assert "# Rubric Content" in prompt
    assert "# Campaign Architecture" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = grid_prophet_loader.build_grid_prophet_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM SKILL TEXT",
    )
    assert "CUSTOM SKILL TEXT" in prompt
    assert "PLMKR MARKETING KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = grid_prophet_loader.build_grid_prophet_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY SKILL TEXT",
    )
    assert "ONLY SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import grid_prophet_loader
    importlib.reload(grid_prophet_loader)

    prompt = grid_prophet_loader.build_grid_prophet_system_prompt()

    assert_no_forbidden_terms(prompt)
