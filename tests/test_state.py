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
