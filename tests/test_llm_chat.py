import openai
import pytest

from src import llm
from tests.fakes import NO_CHOICES, FakeClient, connection_error, status_error

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


def test_get_client_leaves_retries_to_chat_and_caps_wait(monkeypatch):
    monkeypatch.setenv("OPEN_ROUTER", "sk-or-test")
    monkeypatch.setattr(llm, "_client", None)
    built = {}
    monkeypatch.setattr(llm.openai, "OpenAI", lambda **kwargs: built.update(kwargs) or "client")
    assert llm.get_client() == "client"
    assert built["max_retries"] == 0
    assert built["timeout"] == llm.config.LLM_TIMEOUT_SECONDS


def test_chat_retries_reply_without_choices(use_client):
    client = use_client(NO_CHOICES, "ok")
    assert llm.chat("judge", MESSAGES) == "ok"
    assert len(client.calls) == 2


def test_rate_limits_back_off_longer_than_other_failures(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    client = FakeClient(status_error(openai.RateLimitError, 429), status_error(openai.RateLimitError, 429), "ok",
                        connection_error(), "ok")
    monkeypatch.setattr(llm, "get_client", lambda: client)
    assert llm.chat("judge", MESSAGES) == "ok"
    assert sleeps == [10.0, 20.0]
    assert llm.chat("judge", MESSAGES) == "ok"
    assert sleeps[2:] == [1.0]
