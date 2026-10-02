"""OpenRouter access through the OpenAI-compatible client."""
import json
import re
import time

import openai

from src import config

MAX_RETRIES = 2
BACKOFF_SECONDS = 1.0
# Shared OpenRouter provider pools stay overloaded for a while; a 1s retry just hits the same wall.
RATE_LIMIT_BACKOFF_SECONDS = 10.0
_RETRYABLE = (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError)

_client = None


class LLMError(Exception):
    pass


def get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        # chat() owns the retry policy, so the SDK's own retries are turned off.
        _client = openai.OpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.get_api_key(),
            max_retries=0,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
    return _client


def chat(role: str, messages: list[dict], temperature: float = 0.7) -> str:
    if role not in config.MODELS:
        raise ValueError(f"unknown model role '{role}'")
    model = config.MODELS[role]
    client = get_client()

    for attempt in range(MAX_RETRIES + 1):
        wait = BACKOFF_SECONDS
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature
            )
            content = response.choices[0].message.content if response.choices else None
            if content and content.strip():
                return content
            problem = "empty reply"
        except _RETRYABLE as e:
            problem = f"{type(e).__name__}: {e}"
            if isinstance(e, openai.RateLimitError):
                wait = RATE_LIMIT_BACKOFF_SECONDS
        except openai.APIError as e:
            raise LLMError(f"{role} ({model}) failed: {e}") from e
        if attempt < MAX_RETRIES:
            time.sleep(wait * 2**attempt)

    raise LLMError(f"{role} ({model}) gave up after {MAX_RETRIES + 1} attempts: {problem}")


JSON_NUDGE = "Reply again with ONLY a single valid JSON object. No prose, no code fences."
_TRAILING_COMMA = re.compile(r'("(?:\\.|[^"\\])*")|,\s*([}\]])')


def _object_at(text: str, start: int) -> str | None:
    """Return the balanced {...} block opening at text[start], or None if it never closes."""
    depth, in_string, escaped = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _load_object(candidate: str) -> dict | None:
    # Second attempt drops trailing commas; group 1 matches string literals so commas inside them survive.
    for attempt in (candidate, _TRAILING_COMMA.sub(lambda m: m.group(1) or m.group(2), candidate)):
        try:
            parsed = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        return parsed if isinstance(parsed, dict) else None
    return None


def parse_json(text: str) -> dict | None:
    """Return the first JSON object in a model reply, skipping prose and brace text that isn't JSON."""
    text = text or ""
    start = text.find("{")
    while start != -1:
        candidate = _object_at(text, start)
        parsed = _load_object(candidate) if candidate else None
        if parsed is not None:
            return parsed
        start = text.find("{", start + 1)
    return None


def chat_json(role: str, messages: list[dict], temperature: float = 0.2) -> dict | None:
    reply = chat(role, messages, temperature)
    parsed = parse_json(reply)
    if parsed is not None:
        return parsed
    retry = messages + [
        {"role": "assistant", "content": reply},
        {"role": "user", "content": JSON_NUDGE},
    ]
    return parse_json(chat(role, retry, temperature))
