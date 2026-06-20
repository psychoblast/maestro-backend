"""
Tests for ar_scout_loader — context loader for A&R deep assessment.

All tests are mocked/in-process. No network calls.
"""
import json
import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

from entity_wall_terms import assert_no_forbidden_terms


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_knowledge_tree(tmp_path: Path) -> Path:
    """Create a minimal fake skills dir with a manifest and two knowledge files."""
    skills_dir = tmp_path / "skills"
    knowledge_dir = skills_dir / "maestro-ar-scout" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "rubric", "path": "skills/maestro-ar-scout/knowledge/rubric.md",
             "role": "core-doctrine", "required": True, "description": "test rubric"},
            {"id": "song-eval", "path": "skills/maestro-ar-scout/knowledge/song-eval.md",
             "role": "evaluation-method", "required": True, "description": "test song eval"},
        ],
        "load_order": ["rubric", "song-eval"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "rubric.md").write_text("# Rubric Content\nFive pillars.")
    (knowledge_dir / "song-eval.md").write_text("# Song Eval Content\nThree axes.")

    skill_dir = skills_dir / "maestro-ar-scout"
    (skill_dir / "SKILL.md").write_text("# AR-SCOUT SKILL\nYou are Scout.")

    return skills_dir


# ── load_ar_scout_knowledge ────────────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    result = ar_scout_loader.load_ar_scout_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = ar_scout_loader.load_ar_scout_knowledge(skills_dir=skills_dir)

    # Both files present
    assert "# Rubric Content" in result
    assert "# Song Eval Content" in result

    # Rubric appears before song-eval (load order preserved)
    assert result.index("# Rubric Content") < result.index("# Song Eval Content")

    # Section separator present
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    # Remove one file
    (skills_dir / "maestro-ar-scout" / "knowledge" / "song-eval.md").unlink()

    result = ar_scout_loader.load_ar_scout_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result
    assert "# Song Eval Content" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    # Corrupt the manifest: add unknown id to load_order
    manifest_path = skills_dir / "maestro-ar-scout" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = ar_scout_loader.load_ar_scout_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result  # other files still load


# ── build_ar_scout_system_prompt ───────────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = ar_scout_loader.build_ar_scout_system_prompt(skills_dir=skills_dir)
    assert "AR-SCOUT SKILL" in prompt
    assert "PLMKR A&R KNOWLEDGE BASE" in prompt
    assert "# Rubric Content" in prompt
    assert "# Song Eval Content" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = ar_scout_loader.build_ar_scout_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM SKILL TEXT",
    )
    assert "CUSTOM SKILL TEXT" in prompt
    assert "PLMKR A&R KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = ar_scout_loader.build_ar_scout_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY SKILL TEXT",
    )
    assert "ONLY SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import ar_scout_loader
    importlib.reload(ar_scout_loader)

    prompt = ar_scout_loader.build_ar_scout_system_prompt()

    assert_no_forbidden_terms(prompt)
