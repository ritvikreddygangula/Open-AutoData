"""OpenRouter access through the OpenAI-compatible client."""
import time

import openai

from src import config

MAX_RETRIES = 2
BACKOFF_SECONDS = 1.0
_RETRYABLE = (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError)

_client = None


class LLMError(Exception):
    pass


def get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(base_url=config.OPENROUTER_BASE_URL, api_key=config.get_api_key())
    return _client


def chat(role: str, messages: list[dict], temperature: float = 0.7) -> str:
    if role not in config.MODELS:
        raise ValueError(f"unknown model role '{role}'")
    model = config.MODELS[role]
    client = get_client()

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content
            problem = "empty reply"
        except _RETRYABLE as e:
            problem = f"{type(e).__name__}: {e}"
        except openai.APIError as e:
            raise LLMError(f"{role} ({model}) failed: {e}") from e
        if attempt < MAX_RETRIES:
            time.sleep(BACKOFF_SECONDS * 2**attempt)

    raise LLMError(f"{role} ({model}) gave up after {MAX_RETRIES + 1} attempts: {problem}")
