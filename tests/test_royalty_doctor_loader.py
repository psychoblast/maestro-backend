"""
Tests for royalty_doctor_loader — context loader for the royalty-recovery route.

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
    knowledge_dir = skills_dir / "maestro-royalty-doctor" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "recovery-doctrine", "path": "skills/maestro-royalty-doctor/knowledge/doctrine.md",
             "role": "core-doctrine", "required": True, "description": "test doctrine"},
            {"id": "recovery-rubric", "path": "skills/maestro-royalty-doctor/knowledge/rubric.md",
             "role": "scoring-rubric", "required": True, "description": "test rubric"},
        ],
        "load_order": ["recovery-doctrine", "recovery-rubric"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "doctrine.md").write_text("# Recovery Doctrine\nThe unpaid dollar.")
    (knowledge_dir / "rubric.md").write_text("# Recovery Rubric\nSeven dimensions.")

    skill_dir = skills_dir / "maestro-royalty-doctor"
    (skill_dir / "SKILL.md").write_text("# ROYALTY-DOCTOR SKILL\nYou are Doc.")

    return skills_dir


# ── load_royalty_doctor_knowledge ──────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    result = royalty_doctor_loader.load_royalty_doctor_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = royalty_doctor_loader.load_royalty_doctor_knowledge(skills_dir=skills_dir)

    assert "# Recovery Doctrine" in result
    assert "# Recovery Rubric" in result
    # Doctrine appears before rubric (load order preserved)
    assert result.index("# Recovery Doctrine") < result.index("# Recovery Rubric")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-royalty-doctor" / "knowledge" / "rubric.md").unlink()

    result = royalty_doctor_loader.load_royalty_doctor_knowledge(skills_dir=skills_dir)
    assert "# Recovery Doctrine" in result
    assert "# Recovery Rubric" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-royalty-doctor" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = royalty_doctor_loader.load_royalty_doctor_knowledge(skills_dir=skills_dir)
    assert "# Recovery Doctrine" in result


# ── build_royalty_doctor_system_prompt ─────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = royalty_doctor_loader.build_royalty_doctor_system_prompt(skills_dir=skills_dir)
    assert "ROYALTY-DOCTOR SKILL" in prompt
    assert "PLMKR ROYALTY RECOVERY KNOWLEDGE BASE" in prompt
    assert "# Recovery Doctrine" in prompt
    assert "# Recovery Rubric" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = royalty_doctor_loader.build_royalty_doctor_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM RECOVERY SKILL TEXT",
    )
    assert "CUSTOM RECOVERY SKILL TEXT" in prompt
    assert "PLMKR ROYALTY RECOVERY KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = royalty_doctor_loader.build_royalty_doctor_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY RECOVERY SKILL TEXT",
    )
    assert "ONLY RECOVERY SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import royalty_doctor_loader
    importlib.reload(royalty_doctor_loader)

    prompt = royalty_doctor_loader.build_royalty_doctor_system_prompt()

    assert_no_forbidden_terms(prompt)
