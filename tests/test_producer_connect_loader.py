"""
Tests for producer_connect_loader — context loader for the production assessment route.

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
    knowledge_dir = skills_dir / "maestro-producer-connect" / "knowledge"
    knowledge_dir.mkdir(parents=True)

    manifest = {
        "version": "1.0",
        "files": [
            {"id": "production-doctrine", "path": "skills/maestro-producer-connect/knowledge/doctrine.md",
             "role": "core-doctrine", "required": True, "description": "test doctrine"},
            {"id": "production-readiness-rubric", "path": "skills/maestro-producer-connect/knowledge/rubric.md",
             "role": "scoring-rubric", "required": True, "description": "test rubric"},
        ],
        "load_order": ["production-doctrine", "production-readiness-rubric"],
    }
    (knowledge_dir / "MANIFEST.json").write_text(json.dumps(manifest))
    (knowledge_dir / "doctrine.md").write_text("# Production Doctrine\nThe master is the asset.")
    (knowledge_dir / "rubric.md").write_text("# Production Readiness Rubric\nEight dimensions.")

    skill_dir = skills_dir / "maestro-producer-connect"
    (skill_dir / "SKILL.md").write_text("# PRODUCER-CONNECT SKILL\nYou are Beat.")

    return skills_dir


# ── load_producer_connect_knowledge ─────────────────────────────────────────────

def test_load_knowledge_returns_empty_when_no_manifest(tmp_path):
    """Missing manifest → empty string, no crash."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    result = producer_connect_loader.load_producer_connect_knowledge(skills_dir=tmp_path / "nonexistent")
    assert result == ""


def test_load_knowledge_assembles_files_in_order(tmp_path):
    """Files are joined in manifest load_order with section separators."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    skills_dir = _make_knowledge_tree(tmp_path)
    result = producer_connect_loader.load_producer_connect_knowledge(skills_dir=skills_dir)

    assert "# Production Doctrine" in result
    assert "# Production Readiness Rubric" in result
    # Doctrine appears before rubric (load order preserved)
    assert result.index("# Production Doctrine") < result.index("# Production Readiness Rubric")
    assert "---" in result


def test_load_knowledge_skips_missing_file_gracefully(tmp_path):
    """A file listed in the manifest but absent from disk is skipped silently."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    (skills_dir / "maestro-producer-connect" / "knowledge" / "rubric.md").unlink()

    result = producer_connect_loader.load_producer_connect_knowledge(skills_dir=skills_dir)
    assert "# Production Doctrine" in result
    assert "# Production Readiness Rubric" not in result


def test_load_knowledge_skips_unknown_id_in_load_order(tmp_path):
    """An ID in load_order not matching any file entry is skipped safely."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    manifest_path = skills_dir / "maestro-producer-connect" / "knowledge" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["load_order"].insert(0, "no-such-file")
    manifest_path.write_text(json.dumps(manifest))

    result = producer_connect_loader.load_producer_connect_knowledge(skills_dir=skills_dir)
    assert "# Production Doctrine" in result


# ── build_producer_connect_system_prompt ────────────────────────────────────────

def test_build_system_prompt_combines_skill_and_knowledge(tmp_path):
    """System prompt contains skill text followed by the knowledge base header."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = producer_connect_loader.build_producer_connect_system_prompt(skills_dir=skills_dir)
    assert "PRODUCER-CONNECT SKILL" in prompt
    assert "PLMKR PRODUCTION KNOWLEDGE BASE" in prompt
    assert "# Production Doctrine" in prompt
    assert "# Production Readiness Rubric" in prompt


def test_build_system_prompt_accepts_preloaded_skill_text(tmp_path):
    """skill_text kwarg bypasses disk read for the SKILL.md."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    skills_dir = _make_knowledge_tree(tmp_path)

    prompt = producer_connect_loader.build_producer_connect_system_prompt(
        skills_dir=skills_dir,
        skill_text="CUSTOM PRODUCTION SKILL TEXT",
    )
    assert "CUSTOM PRODUCTION SKILL TEXT" in prompt
    assert "PLMKR PRODUCTION KNOWLEDGE BASE" in prompt


def test_build_system_prompt_works_with_no_knowledge(tmp_path):
    """If no manifest/knowledge exists, prompt is just the skill text."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)
    empty_skills = tmp_path / "empty_skills"
    empty_skills.mkdir()

    prompt = producer_connect_loader.build_producer_connect_system_prompt(
        skills_dir=empty_skills,
        skill_text="ONLY PRODUCTION SKILL TEXT",
    )
    assert "ONLY PRODUCTION SKILL TEXT" in prompt
    assert "KNOWLEDGE BASE" not in prompt


def test_build_system_prompt_no_entity_strings_in_real_knowledge():
    """Smoke-test: loading real knowledge files must not contain forbidden strings."""
    import producer_connect_loader
    importlib.reload(producer_connect_loader)

    prompt = producer_connect_loader.build_producer_connect_system_prompt()

    assert_no_forbidden_terms(prompt)
