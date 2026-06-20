"""
Tests for sync_agent_loader — context loader for sync licensing assessment.

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
    knowledge_dir = skills_dir / "maestro-sync-agent" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "scoring-rubric", "path": "skills/maestro-sync-agent/knowledge/rubric.md",
             "role": "core-doctrine", "required": True, "description": "test rubric"},
            {"id": "buyer-psychology", "path": "skills/maestro-sync-agent/knowledge/buyer.md",
             "role": "buyer-intelligence", "required": True, "description": "test buyer psych"},
        ],
        "load_order": ["scoring-rubric", "buyer-psychology"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "rubric.md").write_text("# Rubric Content\nFour dimensions.")
    (knowledge_dir / "buyer.md").write_text("# Buyer Psychology\nFunded vs fishing.")

    skill_dir = skills_dir / "maestro-sync-agent"
    (skill_dir / "SKILL.md").write_text("# SYNC-AGENT SKILL\nYou are Sync.")

    return skills_dir


# ── load_sync_agent_knowledge ──────────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    result = sync_agent_loader.load_sync_agent_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = sync_agent_loader.load_sync_agent_knowledge(skills_dir=skills_dir)

    assert "# Rubric Content" in result
    assert "# Buyer Psychology" in result
    # Rubric appears before buyer psychology (load order preserved)
    assert result.index("# Rubric Content") < result.index("# Buyer Psychology")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-sync-agent" / "knowledge" / "buyer.md").unlink()

    result = sync_agent_loader.load_sync_agent_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result
    assert "# Buyer Psychology" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-sync-agent" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = sync_agent_loader.load_sync_agent_knowledge(skills_dir=skills_dir)
    assert "# Rubric Content" in result


# ── build_sync_agent_system_prompt ────────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = sync_agent_loader.build_sync_agent_system_prompt(skills_dir=skills_dir)
    assert "SYNC-AGENT SKILL" in prompt
    assert "PLMKR SYNC KNOWLEDGE BASE" in prompt
    assert "# Rubric Content" in prompt
    assert "# Buyer Psychology" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = sync_agent_loader.build_sync_agent_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM SYNC SKILL TEXT",
    )
    assert "CUSTOM SYNC SKILL TEXT" in prompt
    assert "PLMKR SYNC KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = sync_agent_loader.build_sync_agent_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY SYNC SKILL TEXT",
    )
    assert "ONLY SYNC SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import sync_agent_loader
    importlib.reload(sync_agent_loader)

    prompt = sync_agent_loader.build_sync_agent_system_prompt()

    assert_no_forbidden_terms(prompt)
