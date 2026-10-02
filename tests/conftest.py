import pytest

from src import llm


@pytest.fixture
def fake_llm(monkeypatch):
    """Install a fake OpenRouter client for llm.chat and skip retry sleeps."""
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)

    def install(client):
        monkeypatch.setattr(llm, "get_client", lambda: client)
        return client

    return install
