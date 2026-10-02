# Agent Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation the LangGraph agent runs on: central config, a chunk loader (SEC CSV → `data/chunks.json`), the `AgentState` + shared record contract, and an OpenRouter client that survives flaky networks and messy JSON.

**Architecture:** Four small modules under `src/`, each with one job and its own test file. Nothing here calls a graph yet; branch `feat/agent-nodes` builds nodes on top of `chat_json()` and `AgentState`, and `feat/agent-graph` wires them. All tests run offline against a scripted fake client.

**Tech Stack:** Python 3.13, langgraph 1.2, openai 3.x (OpenAI-compatible client pointed at OpenRouter), python-dotenv, pytest.

**Spec:** `docs/MASTER_SPEC.md`, `docs/PERSON_1_AGENT_ARCHITECT.md`, `Data_flow.png`, plus the `feat/agent-core` spec approved in chat on 2026-10-02.

## Global Constraints

- Weak solver score `<= 65`, strong solver score `>= 60`, gap (strong − weak) `>= 20`, max `3` revision rounds per chunk.
- OpenRouter base URL `https://openrouter.ai/api/v1`; API key read from env var `OPEN_ROUTER`.
- Model IDs: challenger `z-ai/glm-5.3`, weak `meta-llama/llama-3.2-3b-instruct`, strong `deepseek/deepseek-v4.1-flash`, judge `nvidia/nemotron-3-super-120b-a12b`, final judge `qwen/qwen3.8-2.4t-a95b`.
- Shared record fields (MASTER_SPEC §4): `chunk_id`, `round_num`, `question`, `reference_answer`, `weak_score`, `strong_score`, `score_gap`, `judge_feedback`, `status`.
- Data paths: `data/chunks.json`, `data/trajectories.json`, `data/accepted.json`.
- `src/prompts.py` (Person 3) and `src/snowflake_sync.py` (Person 2) are not created on this branch.
- Never `git push`. Commit messages are one human-written line.

## Review Focus

1. Model reply wraps JSON in prose, ```` ``` ```` fences, or has trailing commas → still parsed into a dict.
2. Model reply contains braces inside JSON strings (e.g. `"{x}"`) or a second object afterwards → the first complete object is returned intact.
3. Model returns empty/`None` content (common with reasoning models on OpenRouter) → retried, then a clear `LLMError`, never a silent `""`.
4. `OPEN_ROUTER` missing → modules still import; the first API call raises a `ConfigError` naming the variable.
5. CSV chunk text full of `\u200b` filler lines, chunks that are empty after cleaning, or duplicate `chunk_id`s → text is cleaned, empties skipped, duplicates rejected loudly.

Each is pinned by a test in the owning task below.

---

## File Structure

| File | Responsibility |
|---|---|
| `requirements.txt` | Pinned runtime + test deps |
| `pytest.ini` | Puts repo root on `sys.path` |
| `src/__init__.py` | Package marker |
| `src/config.py` | Env loading, model IDs, thresholds, paths, `get_api_key()` |
| `src/chunks.py` | `clean_text`, `load_chunks`, `write_chunks_json`, CSV→JSON CLI |
| `src/state.py` | `AgentState`, `initial_state`, `to_record`, `RECORD_FIELDS` |
| `src/llm.py` | `chat`, `parse_json`, `chat_json`, `LLMError` |
| `tests/fakes.py` | `FakeClient` that replays scripted replies/exceptions |
| `tests/test_*.py` | One test file per module |
| `data/chunks.json` | Generated from `SUNHACKS_2026-10-02-1234.csv` |

---

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `src/__init__.py`, `tests/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write the files**

`requirements.txt`
```
langgraph==1.2.12
openai==3.24.0
python-dotenv==1.2.4
pytest==9.1.1
```

`pytest.ini`
```ini
[pytest]
pythonpath = .
testpaths = tests
```

`.gitignore` (append)
```
.venv/
__pycache__/
.pytest_cache/
.DS_Store
```

`src/__init__.py` and `tests/__init__.py`: empty.

- [ ] **Step 2: Verify pytest runs**

Run: `.venv/bin/pytest`
Expected: `no tests ran` (exit 5), no import errors.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt pytest.ini .gitignore src/__init__.py tests/__init__.py docs/superpowers/plans/2026-10-02-agent-core.md
git commit -m "Set up Python project skeleton and agent core plan"
```

---

### Task 2: Central config

**Files:**
- Create: `src/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `MODELS: dict[str, str]` with keys `challenger`, `weak`, `strong`, `judge`, `final_judge`; `WEAK_MAX`, `STRONG_MIN`, `GAP_MIN`, `MAX_ROUNDS`, `SOLVER_SAMPLES` (ints); `OPENROUTER_BASE_URL: str`; `DATA_DIR`, `CHUNKS_PATH`, `TRAJECTORIES_PATH`, `ACCEPTED_PATH` (`Path`); `get_api_key() -> str`; `ConfigError(Exception)`.

- [ ] **Step 1: Write the failing tests**

```python
import importlib

import pytest

from src import config


def test_thresholds_match_master_spec():
    assert (config.WEAK_MAX, config.STRONG_MIN, config.GAP_MIN, config.MAX_ROUNDS) == (65, 60, 20, 3)


def test_default_models_match_data_flow():
    assert config.MODELS == {
        "challenger": "z-ai/glm-5.3",
        "weak": "meta-llama/llama-3.2-3b-instruct",
        "strong": "deepseek/deepseek-v4.1-flash",
        "judge": "nvidia/nemotron-3-super-120b-a12b",
        "final_judge": "qwen/qwen3.8-2.4t-a95b",
    }


def test_model_can_be_overridden_from_env(monkeypatch):
    monkeypatch.setenv("MODEL_WEAK", "some/other-model")
    try:
        assert importlib.reload(config).MODELS["weak"] == "some/other-model"
    finally:
        monkeypatch.delenv("MODEL_WEAK")
        importlib.reload(config)


def test_get_api_key_strips_whitespace(monkeypatch):
    monkeypatch.setenv("OPEN_ROUTER", "  sk-or-test \n")
    assert config.get_api_key() == "sk-or-test"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_get_api_key_names_the_missing_variable(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("OPEN_ROUTER", raising=False)
    else:
        monkeypatch.setenv("OPEN_ROUTER", value)
    with pytest.raises(config.ConfigError, match="OPEN_ROUTER"):
        config.get_api_key()
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: collection error `ImportError: cannot import name 'config'`.

- [ ] **Step 3: Implement**

```python
"""Central configuration: model IDs, acceptance thresholds, data paths."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "challenger": os.getenv("MODEL_CHALLENGER", "z-ai/glm-5.3"),
    "weak": os.getenv("MODEL_WEAK", "meta-llama/llama-3.2-3b-instruct"),
    "strong": os.getenv("MODEL_STRONG", "deepseek/deepseek-v4.1-flash"),
    "judge": os.getenv("MODEL_JUDGE", "nvidia/nemotron-3-super-120b-a12b"),
    "final_judge": os.getenv("MODEL_FINAL_JUDGE", "qwen/qwen3.8-2.4t-a95b"),
}

# Acceptance gate (MASTER_SPEC §2). Scores are 0-100.
WEAK_MAX = 65
STRONG_MIN = 60
GAP_MIN = 20
MAX_ROUNDS = 3
SOLVER_SAMPLES = 3

DATA_DIR = ROOT / "data"
CHUNKS_PATH = DATA_DIR / "chunks.json"
TRAJECTORIES_PATH = DATA_DIR / "trajectories.json"
ACCEPTED_PATH = DATA_DIR / "accepted.json"


class ConfigError(Exception):
    pass


def get_api_key() -> str:
    key = (os.getenv("OPEN_ROUTER") or "").strip()
    if not key:
        raise ConfigError("OPEN_ROUTER is not set; add it to .env")
    return key
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "Add central config with model IDs and acceptance thresholds"
```

---

### Task 3: Chunk loader and CSV → JSON conversion

**Files:**
- Create: `src/chunks.py`, `data/chunks.json` (generated)
- Test: `tests/test_chunks.py`

**Interfaces:**
- Produces: `clean_text(text: str) -> str`; `load_chunks(path: str | Path) -> list[dict]` where each dict is `{"chunk_id": str, "text": str, "doc_id": str | None, "adsh": str | None}`; `write_chunks_json(chunks: list[dict], path: str | Path) -> None`; CLI `python -m src.chunks <in.csv> [out.json]` (default out = `config.CHUNKS_PATH`).

- [ ] **Step 1: Write the failing tests**

```python
import json

import pytest

from src.chunks import clean_text, load_chunks, write_chunks_json

HEADER = "CHUNK_ID,SEC_DOCUMENT_ID,ADSH,CHUNK_TEXT\n"


def write_csv(tmp_path, body):
    path = tmp_path / "chunks.csv"
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_clean_text_drops_zero_width_filler_lines():
    raw = "RESULTS\n\u200b\n\u200b\n\u200b\nRevenue rose 4%.\u00a0Net income fell.  \n"
    assert clean_text(raw) == "RESULTS\n\nRevenue rose 4%. Net income fell."


def test_load_csv_maps_snowflake_columns(tmp_path):
    path = write_csv(tmp_path, '4,doc-1,adsh-1,"Revenue was $86.3 million."\n')
    assert load_chunks(path) == [
        {"chunk_id": "4", "text": "Revenue was $86.3 million.", "doc_id": "doc-1", "adsh": "adsh-1"}
    ]


def test_load_csv_accepts_lowercase_headers(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("chunk_id,chunk_text\n1,hello\n", encoding="utf-8")
    assert load_chunks(path)[0]["text"] == "hello"


def test_load_skips_chunks_empty_after_cleaning(tmp_path):
    path = write_csv(tmp_path, '1,d,a,"\u200b\n\u200b"\n2,d,a,real text\n')
    assert [c["chunk_id"] for c in load_chunks(path)] == ["2"]


def test_load_rejects_duplicate_chunk_ids(tmp_path):
    path = write_csv(tmp_path, "1,d,a,one\n1,d,a,two\n")
    with pytest.raises(ValueError, match="duplicate chunk_id 1"):
        load_chunks(path)


def test_load_rejects_csv_without_text_column(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("CHUNK_ID,BODY\n1,x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CHUNK_TEXT"):
        load_chunks(path)


def test_json_round_trip(tmp_path):
    chunks = [{"chunk_id": "7", "text": "Some text", "doc_id": None, "adsh": None}]
    out = tmp_path / "nested" / "chunks.json"
    write_chunks_json(chunks, out)
    assert json.loads(out.read_text())[0]["chunk_id"] == "7"
    assert load_chunks(out) == chunks


def test_load_rejects_unknown_extension(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("x")
    with pytest.raises(ValueError, match=".txt"):
        load_chunks(path)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_chunks.py -v`
Expected: `ModuleNotFoundError: No module named 'src.chunks'`.

- [ ] **Step 3: Implement**

```python
"""Load SEC text chunks from the Snowflake CSV export or data/chunks.json."""
import csv
import json
import re
import sys
from pathlib import Path

from src import config

_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)


def clean_text(text: str) -> str:
    text = text.translate(_INVISIBLE).replace("\u00a0", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _from_csv(path: Path) -> list[dict]:
    csv.field_size_limit(sys.maxsize)
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = [{k.strip().upper(): v for k, v in row.items()} for row in csv.DictReader(f)]
    if rows and not {"CHUNK_ID", "CHUNK_TEXT"} <= rows[0].keys():
        raise ValueError(f"{path} needs CHUNK_ID and CHUNK_TEXT columns")
    return [
        {
            "chunk_id": row["CHUNK_ID"].strip(),
            "text": row["CHUNK_TEXT"],
            "doc_id": row.get("SEC_DOCUMENT_ID"),
            "adsh": row.get("ADSH"),
        }
        for row in rows
    ]


def load_chunks(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".csv":
        raw = _from_csv(path)
    elif path.suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"unsupported chunk file type {path.suffix}")

    chunks, seen = [], set()
    for item in raw:
        chunk_id = str(item["chunk_id"])
        if chunk_id in seen:
            raise ValueError(f"duplicate chunk_id {chunk_id} in {path}")
        seen.add(chunk_id)
        text = clean_text(item["text"])
        if text:
            chunks.append({**item, "chunk_id": chunk_id, "text": text})
    return chunks


def write_chunks_json(chunks: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: python -m src.chunks <in.csv> [out.json]")
    out = sys.argv[2] if len(sys.argv) == 3 else config.CHUNKS_PATH
    chunks = load_chunks(sys.argv[1])
    write_chunks_json(chunks, out)
    print(f"wrote {len(chunks)} chunks to {out}")
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/test_chunks.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add src/chunks.py tests/test_chunks.py
git commit -m "Add chunk loader that cleans and converts the SEC CSV"
```

- [ ] **Step 6: Generate `data/chunks.json` and commit**

Run: `.venv/bin/python -m src.chunks SUNHACKS_2026-10-02-1234.csv`
Expected: `wrote 27 chunks to .../data/chunks.json` (fewer only if some are empty after cleaning; check `grep -c '\\u200b' data/chunks.json` is 0).

```bash
git add data/chunks.json
git commit -m "Generate chunks.json from the Snowflake SEC export"
```

---

### Task 4: Agent state and record contract

**Files:**
- Create: `src/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: `Status = Literal["PENDING", "REVISE", "ACCEPTED", "REJECTED"]`; `AgentState(TypedDict, total=False)` with `chunk_id: str`, `chunk_text: str`, `round_num: int`, `question: str`, `reference_answer: str`, `weak_answers: list[str]`, `strong_answers: list[str]`, `weak_score: float`, `strong_score: float`, `score_gap: float`, `judge_feedback: str`, `status: Status`, `fail_reason: str`; `initial_state(chunk_id: str, chunk_text: str) -> AgentState` (round_num `0`; `node_challenger` increments it); `RECORD_FIELDS: tuple[str, ...]`; `to_record(state: AgentState) -> dict`.

- [ ] **Step 1: Write the failing tests**

```python
import json

from src.state import RECORD_FIELDS, initial_state, to_record

CONTRACT = (
    "chunk_id", "round_num", "question", "reference_answer",
    "weak_score", "strong_score", "score_gap", "judge_feedback", "status",
)


def test_initial_state_starts_pending_before_round_one():
    state = initial_state("4", "Revenue rose.")
    assert state["chunk_id"] == "4"
    assert state["chunk_text"] == "Revenue rose."
    assert state["round_num"] == 0
    assert state["status"] == "PENDING"
    assert state["weak_answers"] == [] and state["strong_answers"] == []


def test_record_fields_are_master_spec_contract_plus_extras():
    assert RECORD_FIELDS == CONTRACT + ("fail_reason", "timestamp")


def test_to_record_keeps_only_contract_fields():
    state = {
        **initial_state("4", "long chunk text"),
        "round_num": 2, "question": "Q?", "reference_answer": "A",
        "weak_answers": ["w"], "strong_answers": ["s"],
        "weak_score": 40.0, "strong_score": 80.0, "score_gap": 40.0,
        "judge_feedback": "good", "status": "ACCEPTED",
    }
    record = to_record(state)
    assert tuple(record) == RECORD_FIELDS
    assert record["score_gap"] == 40.0 and record["status"] == "ACCEPTED"
    assert "chunk_text" not in record and "weak_answers" not in record


def test_to_record_fills_missing_fields_with_none_and_is_json_safe():
    record = to_record(initial_state("9", "t"))
    assert record["question"] is None and record["weak_score"] is None
    assert record["timestamp"].endswith("+00:00")
    json.dumps(record)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_state.py -v`
Expected: `ModuleNotFoundError: No module named 'src.state'`.

- [ ] **Step 3: Implement**

```python
"""LangGraph state for one chunk, and the shared JSON record (MASTER_SPEC §4)."""
from datetime import datetime, timezone
from typing import Literal, TypedDict

Status = Literal["PENDING", "REVISE", "ACCEPTED", "REJECTED"]


class AgentState(TypedDict, total=False):
    chunk_id: str
    chunk_text: str
    round_num: int
    question: str
    reference_answer: str
    weak_answers: list[str]
    strong_answers: list[str]
    weak_score: float
    strong_score: float
    score_gap: float
    judge_feedback: str
    status: Status
    fail_reason: str


RECORD_FIELDS = (
    "chunk_id", "round_num", "question", "reference_answer",
    "weak_score", "strong_score", "score_gap", "judge_feedback", "status",
    "fail_reason", "timestamp",
)


def initial_state(chunk_id: str, chunk_text: str) -> AgentState:
    return {
        "chunk_id": chunk_id,
        "chunk_text": chunk_text,
        "round_num": 0,
        "weak_answers": [],
        "strong_answers": [],
        "status": "PENDING",
    }


def to_record(state: AgentState) -> dict:
    record = {field: state.get(field) for field in RECORD_FIELDS}
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    return record
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/test_state.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/state.py tests/test_state.py
git commit -m "Add agent state and shared trajectory record contract"
```

---

### Task 5: OpenRouter chat client with retries

**Files:**
- Create: `src/llm.py`, `tests/fakes.py`
- Test: `tests/test_llm_chat.py`

**Interfaces:**
- Consumes: `config.MODELS`, `config.OPENROUTER_BASE_URL`, `config.get_api_key()`.
- Produces: `LLMError(Exception)`; `get_client() -> openai.OpenAI` (lazy singleton); `chat(role: str, messages: list[dict], temperature: float = 0.7) -> str`. Retries `APIConnectionError` (incl. timeouts), `RateLimitError`, `InternalServerError` and empty content up to `MAX_RETRIES = 2` extra attempts with `time.sleep(BACKOFF_SECONDS * 2**attempt)`; other `openai.APIError`s raise `LLMError` immediately. Unknown role → `ValueError`.

- [ ] **Step 1: Write the fake client**

`tests/fakes.py`
```python
"""Scripted stand-in for openai.OpenAI used by llm tests."""
from types import SimpleNamespace

import httpx
import openai

REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def connection_error():
    return openai.APIConnectionError(request=REQUEST)


def status_error(cls, code):
    return cls("boom", response=httpx.Response(code, request=REQUEST), body=None)


class FakeClient:
    """Each call pops the next scripted reply: a string, None, or an exception."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        message = SimpleNamespace(content=reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
```

- [ ] **Step 2: Write the failing tests**

`tests/test_llm_chat.py`
```python
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
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/pytest tests/test_llm_chat.py -v`
Expected: `ModuleNotFoundError: No module named 'src.llm'`.

- [ ] **Step 4: Implement**

`src/llm.py`
```python
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
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/pytest tests/test_llm_chat.py -v`
Expected: 9 passed.

- [ ] **Step 6: Commit**

```bash
git add src/llm.py tests/fakes.py tests/test_llm_chat.py
git commit -m "Add OpenRouter chat client with retries for flaky calls"
```

---

### Task 6: Tolerant JSON parsing

**Files:**
- Modify: `src/llm.py` (append)
- Test: `tests/test_llm_json.py`

**Interfaces:**
- Consumes: `chat()` from Task 5.
- Produces: `parse_json(text: str) -> dict | None`; `chat_json(role: str, messages: list[dict], temperature: float = 0.2) -> dict | None` — one re-ask with a "JSON only" nudge if the first reply doesn't parse; returns `None` if the second doesn't either; `LLMError` from `chat()` propagates.

- [ ] **Step 1: Write the failing tests**

`tests/test_llm_json.py`
```python
import pytest

from src import llm
from src.llm import parse_json
from tests.fakes import FakeClient


@pytest.mark.parametrize("text", [
    '{"score": 80}',
    '```json\n{"score": 80}\n```',
    'Sure! Here is the result:\n{"score": 80}\nHope that helps.',
    '{"score": 80,}',
])
def test_parse_json_tolerates_common_model_noise(text):
    assert parse_json(text) == {"score": 80}


def test_parse_json_respects_braces_inside_strings():
    text = 'Result: {"question": "What is {x} in \\"Q1\\"?", "n": {"a": 1}} and {"other": 2}'
    assert parse_json(text) == {"question": 'What is {x} in "Q1"?', "n": {"a": 1}}


def test_parse_json_keeps_commas_inside_strings():
    assert parse_json('{"a": "x,}", "b": 1}') == {"a": "x,}", "b": 1}


@pytest.mark.parametrize("text", ["no json here", '{"a": 1', "[1, 2]", ""])
def test_parse_json_returns_none_when_no_object(text):
    assert parse_json(text) is None


def test_chat_json_reasks_once_when_reply_is_not_json(monkeypatch):
    client = FakeClient("I think the answer is 42", '{"answer": 42}')
    monkeypatch.setattr(llm, "get_client", lambda: client)
    assert llm.chat_json("judge", [{"role": "user", "content": "grade"}]) == {"answer": 42}
    retry_messages = client.calls[1]["messages"]
    assert retry_messages[-2] == {"role": "assistant", "content": "I think the answer is 42"}
    assert "JSON" in retry_messages[-1]["content"]


def test_chat_json_returns_none_after_second_bad_reply(monkeypatch):
    client = FakeClient("nope", "still nope")
    monkeypatch.setattr(llm, "get_client", lambda: client)
    assert llm.chat_json("judge", [{"role": "user", "content": "grade"}]) is None
    assert len(client.calls) == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_llm_json.py -v`
Expected: `ImportError: cannot import name 'parse_json'`.

- [ ] **Step 3: Implement (append to `src/llm.py`, add `import json`, `import re` at top)**

```python
JSON_NUDGE = "Reply again with ONLY a single valid JSON object. No prose, no code fences."
_TRAILING_COMMA = re.compile(r'("(?:\\.|[^"\\])*")|,\s*([}\]])')


def _first_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
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


def parse_json(text: str) -> dict | None:
    candidate = _first_object(text or "")
    if candidate is None:
        return None
    for attempt in (candidate, _TRAILING_COMMA.sub(lambda m: m.group(1) or m.group(2), candidate)):
        try:
            parsed = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        return parsed if isinstance(parsed, dict) else None
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
```

- [ ] **Step 4: Run full suite**

Run: `.venv/bin/pytest -v`
Expected: all tests pass (config 7, chunks 8, state 4, chat 9, json 12 = 40).

- [ ] **Step 5: Commit**

```bash
git add src/llm.py tests/test_llm_json.py
git commit -m "Add tolerant JSON parsing for model replies"
```

---

### Task 7: Live smoke check (manual, no commit)

- [ ] **Step 1:** `.venv/bin/python -c "from src.llm import chat_json; print(chat_json('weak', [{'role':'user','content':'Return {\"ok\": true} as JSON.'}]))"`
Expected: `{'ok': True}`. If OpenRouter returns a 404 for a model ID, report which role; do not change IDs without the human's say-so.
