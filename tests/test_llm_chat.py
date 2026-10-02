import openai
import pytest

from src import llm
from tests.fakes import FakeClient, connection_error, status_error

MESSAGES = [{"role": "user", "content": "hi"}]


@pytest.fixture
def use_client(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)

    def install(*replies):
        client = FakeClient(*replies)
        monkeypatch.setattr(llm, "get_client", lambda: client)
        return client

    return install


def test_chat_sends_role_model_and_returns_content(use_client):
    client = use_client("hello")
    assert llm.chat("weak", MESSAGES, temperature=0.3) == "hello"
    call = client.calls[0]
    assert call["model"] == "meta-llama/llama-3.2-3b-instruct"
    assert call["messages"] == MESSAGES and call["temperature"] == 0.3


def test_chat_rejects_unknown_role(use_client):
    use_client()
    with pytest.raises(ValueError, match="unknown model role 'oracle'"):
        llm.chat("oracle", MESSAGES)


@pytest.mark.parametrize("failure", [
    connection_error(),
    status_error(openai.RateLimitError, 429),
    status_error(openai.InternalServerError, 502),
])
def test_chat_retries_transient_failures(use_client, failure):
    client = use_client(failure, "ok")
    assert llm.chat("judge", MESSAGES) == "ok"
    assert len(client.calls) == 2


def test_chat_retries_empty_content_then_raises(use_client):
    client = use_client(None, "", "   ")
    with pytest.raises(llm.LLMError, match="empty"):
        llm.chat("judge", MESSAGES)
    assert len(client.calls) == 3


def test_chat_gives_up_after_three_attempts(use_client):
    client = use_client(connection_error(), connection_error(), connection_error(), "late")
    with pytest.raises(llm.LLMError, match="judge"):
        llm.chat("judge", MESSAGES)
    assert len(client.calls) == 3


def test_chat_does_not_retry_auth_errors(use_client):
    client = use_client(status_error(openai.AuthenticationError, 401), "ok")
    with pytest.raises(llm.LLMError):
        llm.chat("judge", MESSAGES)
    assert len(client.calls) == 1


def test_get_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPEN_ROUTER", raising=False)
    monkeypatch.setattr(llm, "_client", None)
    with pytest.raises(llm.config.ConfigError, match="OPEN_ROUTER"):
        llm.get_client()
