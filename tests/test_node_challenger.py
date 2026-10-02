from src.default_prompts import DEFAULTS
from src.nodes import node_challenger
from tests.fakes import FakeClient, connection_error
from tests.samples import CHALLENGER, CHUNK, as_json, chunk_state, package, rubric


def test_first_round_writes_the_full_package_from_the_filing(fake_llm):
    client = fake_llm(FakeClient(as_json(package())))
    update = node_challenger(chunk_state())

    call = client.calls[0]
    assert call["model"] == CHALLENGER
    assert call["messages"][0] == {"role": "system", "content": DEFAULTS["CHALLENGER_SYSTEM"]}
    user = call["messages"][1]["content"]
    assert f"<filing>\n{CHUNK}\n</filing>" in user
    assert "ENTIRELY NEW" not in user

    assert update["round_num"] == 1
    assert update["context"] == package()["context"]
    assert update["rubric"] == rubric()
    assert update["skill_tags"] == ["multi_step_calculation", "causal_reasoning"]
    assert update["status"] == "PENDING" and update["error"] is None


def test_new_round_clears_the_previous_rounds_results(fake_llm):
    fake_llm(FakeClient(as_json(package())))
    stale = chunk_state(round_num=1, weak_answers=["old"], weak_score=80.0, failure_mode="TOO_EASY")
    update = node_challenger(stale)
    assert update["round_num"] == 2
    assert update["weak_answers"] == [] and update["strong_attempt_scores"] == []
    assert update["weak_score"] is None and update["failure_mode"] is None


def test_refinement_lists_failed_questions_by_failure_mode(fake_llm):
    client = fake_llm(FakeClient(as_json(package())))
    history = [
        {"round_num": 1, "question": "What were net sales?", "failure_mode": "TOO_EASY",
         "fail_reason": "weak_score 80.0 > 65"},
        {"round_num": 2, "question": "Why did costs rise?", "failure_mode": "FAILED_QV",
         "fail_reason": "context leaks the answer"},
        {"round_num": 3, "question": "Forecast 2027 margin", "failure_mode": "FAILED_ON_STRONG",
         "fail_reason": "strong_score 40.0 < 60"},
        {"round_num": 4, "question": "Reconcile every line item", "failure_mode": "TOO_HARD",
         "fail_reason": "a weak attempt scored 0"},
    ]
    node_challenger(chunk_state(round_num=3, history=history))
    user = client.calls[0]["messages"][1]["content"]
    assert 'TOO EASY' in user and '- Round 1: "What were net sales?" (weak_score 80.0 > 65)' in user
    assert 'FAILED QUALITY CHECK' in user and "context leaks the answer" in user
    assert 'FAILED ON STRONG' in user and "strong_score 40.0 < 60" in user
    assert 'TOO HARD' in user and "Reconcile every line item" in user
    assert "ENTIRELY NEW question from a DIFFERENT angle" in user


def test_rubric_breaking_the_rules_gets_one_correction_request(fake_llm):
    client = fake_llm(FakeClient(as_json(package(rubric=rubric(9))), as_json(package())))
    update = node_challenger(chunk_state())
    assert update["rubric"] == rubric()
    correction = client.calls[1]["messages"][-1]["content"]
    assert "rubric" in correction and "10-15" in correction


def test_missing_field_twice_ends_the_chunk_with_an_error(fake_llm):
    bad = as_json(package(context=""))
    fake_llm(FakeClient(bad, bad))
    update = node_challenger(chunk_state())
    assert update["round_num"] == 1
    assert update["error"].startswith("challenger:") and "context" in update["error"]


def test_model_failure_ends_the_chunk_with_an_error(fake_llm):
    fake_llm(FakeClient(connection_error(), connection_error(), connection_error()))
    update = node_challenger(chunk_state())
    assert update["error"].startswith("challenger:")
