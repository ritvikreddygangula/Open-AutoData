"""Scripted stand-in for openai.OpenAI used by llm tests."""
from types import SimpleNamespace

import httpx
import openai

NO_CHOICES = object()  # OpenRouter can return 200 with an error body and no choices

REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def connection_error():
    return openai.APIConnectionError(request=REQUEST)


def status_error(cls, code):
    return cls("boom", response=httpx.Response(code, request=REQUEST), body=None)


class FakeClient:
    """Each call pops the next scripted reply: a string, None, NO_CHOICES, or an exception."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if reply is NO_CHOICES:
            return SimpleNamespace(choices=None)
        message = SimpleNamespace(content=reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
