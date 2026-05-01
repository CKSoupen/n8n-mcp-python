import pytest

from n8n_mcp.config import Config


def test_from_env_requires_both(monkeypatch):
    monkeypatch.delenv("N8N_BASE_URL", raising=False)
    monkeypatch.delenv("N8N_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.example.com/")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    cfg = Config.from_env()
    assert cfg.base_url == "https://n8n.example.com"
    assert cfg.api_key == "tok"
