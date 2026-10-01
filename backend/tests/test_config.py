import importlib
import pathlib

import pytest

import config


def test_require_gemini_key_raises_when_missing(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    with pytest.raises(RuntimeError):
        config.require_gemini_key()


def test_require_gemini_key_returns_value_when_set(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "abc123")
    assert config.require_gemini_key() == "abc123"


def test_chroma_path_is_absolute_not_cwd_relative():
    assert pathlib.Path(config.CHROMA_PATH).is_absolute()


def test_require_ollama_key_raises_when_missing(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_API_KEY", None)
    with pytest.raises(RuntimeError):
        config.require_ollama_key()


def test_require_ollama_key_returns_value_when_set(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_API_KEY", "abc123")
    assert config.require_ollama_key() == "abc123"


def test_allowed_origins_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    # Stop config's import-time load_dotenv from re-reading a local .env.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    try:
        importlib.reload(config)
        assert config.ALLOWED_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]
    finally:
        monkeypatch.undo()
        importlib.reload(config)
