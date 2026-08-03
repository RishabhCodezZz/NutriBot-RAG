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
