import json

from src.default_prompts import DEFAULTS
from src.nodes import node_verifier
from tests.fakes import FakeClient, connection_error
from tests.samples import CHUNK, VERIFIER, as_json, package, ready_state

GOOD = {"leakage": "NO_LEAKAGE", "question_quality": "GOOD", "rubric_quality": "PASS",
        "type_consistency": "CONSISTENT", "feedback": ""}


def test_passes_when_all_four_checks_are_good(fake_llm):
    client = fake_llm(FakeClient(as_json(GOOD)))
    assert node_verifier(ready_state()) == {"verifier_verdict": "PASS", "verifier_feedback": ""}

    call = client.calls[0]
    assert call["model"] == VERIFIER and call["temperature"] == 0
    assert call["messages"][0]["content"] == DEFAULTS["VERIFIER_SYSTEM"]
    user = call["messages"][1]["content"]
    assert CHUNK in user
    sent = json.loads(user.split("PACKAGE:\n", 1)[1])
    assert sent == {k: package()[k] for k in ("question_type", "context", "question", "rubric")}


def test_reference_answer_is_not_shown_to_the_verifier(fake_llm):
    client = fake_llm(FakeClient(as_json(GOOD)))
    node_verifier(ready_state())
    assert package()["reference_answer"] not in client.calls[0]["messages"][1]["content"]


def test_fails_with_the_failed_checks_and_model_feedback(fake_llm):
    reply = {**GOOD, "leakage": "LEAKS_ANSWER", "question_quality": "recall",
             "feedback": "Context states the margin outright."}
    fake_llm(FakeClient(as_json(reply)))
    update = node_verifier(ready_state())
    assert update["verifier_verdict"] == "FAIL"
    assert update["verifier_feedback"] == (
        "leakage: LEAKS_ANSWER; question_quality: RECALL: Context states the margin outright."
    )


def test_unrecognised_check_value_is_an_error(fake_llm):
    fake_llm(FakeClient(as_json({**GOOD, "rubric_quality": "MOSTLY"})))
    assert node_verifier(ready_state())["error"].startswith("verifier:")


def test_model_failure_is_an_error(fake_llm):
    fake_llm(FakeClient(connection_error(), connection_error(), connection_error()))
    assert node_verifier(ready_state())["error"].startswith("verifier:")
