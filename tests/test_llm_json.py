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
