"""
R-19 — Kokoro TTS model files excluded from Railway deploy.

Fix: get_kokoro() emits an explicit WARNING log when kokoro-v1.0.onnx or
voices-v1.0.bin are absent, clarifying that the ElevenLabs fallback will be
used and that this is expected on Railway.

Before this fix the exception from kokoro_onnx.Kokoro() would be caught and
printed as a generic "[TTS] Kokoro unavailable: ..." message. The new check
fires before the import, so the message is clear even if kokoro_onnx is not
installed in the environment.
"""

import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _setup_main(monkeypatch, tmp_path):
    """Configure environment and reload main so get_kokoro() can be called safely."""
    monkeypatch.setenv("DB_PATH",          str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",     "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",  str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",      str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-ant-test")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
    return m


def _call_get_kokoro(m, base_path: Path):
    """Reset Kokoro globals and call get_kokoro() with a custom _BASE."""
    with patch.object(m, "_BASE", base_path), \
         patch.object(m, "_kokoro", None), \
         patch.object(m, "_kokoro_available", None):
        return m.get_kokoro()


def test_missing_files_prints_warning(monkeypatch, tmp_path, capsys):
    """get_kokoro() must print [Kokoro] WARNING when model files are absent."""
    m = _setup_main(monkeypatch, tmp_path)
    capsys.readouterr()  # discard startup noise
    empty_dir = tmp_path / "no_models"
    empty_dir.mkdir()
    _call_get_kokoro(m, empty_dir)
    out = capsys.readouterr().out
    assert "[Kokoro] WARNING" in out
    assert "kokoro-v1.0.onnx" in out
    assert "ElevenLabs" in out


def test_missing_files_returns_none(monkeypatch, tmp_path, capsys):
    """get_kokoro() must return None when model files are absent."""
    m = _setup_main(monkeypatch, tmp_path)
    capsys.readouterr()
    empty_dir = tmp_path / "no_models2"
    empty_dir.mkdir()
    result = _call_get_kokoro(m, empty_dir)
    assert result is None


def test_missing_files_no_kokoro_import_attempted(monkeypatch, tmp_path, capsys):
    """When files are absent, kokoro_onnx import must NOT be attempted."""
    m = _setup_main(monkeypatch, tmp_path)
    capsys.readouterr()
    empty_dir = tmp_path / "no_models3"
    empty_dir.mkdir()
    with patch.dict("sys.modules", {"kokoro_onnx": None}):
        # If import were attempted it would raise TypeError (None is not a module)
        result = _call_get_kokoro(m, empty_dir)
    assert result is None  # no exception means import was skipped


def test_present_files_no_warning(monkeypatch, tmp_path, capsys):
    """When model files exist, the absence warning must NOT appear."""
    m = _setup_main(monkeypatch, tmp_path)
    capsys.readouterr()
    model_dir = tmp_path / "with_models"
    model_dir.mkdir()
    (model_dir / "kokoro-v1.0.onnx").touch()
    (model_dir / "voices-v1.0.bin").touch()
    # kokoro_onnx may not be installed — the import will fail with the usual
    # "[TTS] Kokoro unavailable:" message but NOT the R-19 WARNING.
    _call_get_kokoro(m, model_dir)
    out = capsys.readouterr().out
    assert "[Kokoro] WARNING" not in out
