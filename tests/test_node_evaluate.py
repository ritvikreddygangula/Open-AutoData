import pytest

from src.nodes import node_evaluate
from tests.samples import ready_state


def judged(weak, strong=(), **overrides):
    """State after verification and judging, with scores per attempt."""
    state = ready_state(verifier_verdict="PASS", weak_attempt_scores=list(weak),
                        weak_score=round(sum(weak) / len(weak), 1), **overrides)
    if strong:
        state.update(strong_attempt_scores=list(strong), strong_score=round(sum(strong) / len(strong), 1))
    return state


def test_accepts_a_question_that_separates_the_solvers():
    update = node_evaluate(judged([40, 50, 45], [80, 85, 90]))
    assert update == {"status": "ACCEPTED", "score_gap": 40.0, "failure_mode": None, "fail_reason": None}


def test_accepts_exactly_at_the_boundaries():
    assert node_evaluate(judged([65, 65, 65], [85, 85, 85]))["status"] == "ACCEPTED"


def test_weak_solver_doing_too_well_is_too_easy_without_strong_scores():
    update = node_evaluate(judged([70, 70, 70]))
    assert update["status"] == "REVISE" and update["failure_mode"] == "TOO_EASY"
    assert update["fail_reason"] == "weak_score 70.0 > 65"
    assert update["score_gap"] is None
    assert update["history"] == [{"round_num": 1, "question": ready_state()["question"],
                                  "failure_mode": "TOO_EASY", "fail_reason": "weak_score 70.0 > 65"}]


def test_strong_solver_saturating_is_too_easy():
    update = node_evaluate(judged([40, 40, 40], [96, 96, 96]))
    assert update["failure_mode"] == "TOO_EASY" and update["fail_reason"] == "strong_score 96.0 >= 95"


def test_small_gap_fails_on_strong():
    update = node_evaluate(judged([50, 50, 50], [60, 60, 60]))
    assert update["failure_mode"] == "FAILED_ON_STRONG"
    assert update["fail_reason"] == "score_gap 10.0 < 20" and update["score_gap"] == 10.0


def test_failed_quality_check_is_fed_back_with_the_verifier_feedback():
    state = ready_state(verifier_verdict="FAIL", verifier_feedback="leakage: LEAKS_ANSWER")
    update = node_evaluate(state)
    assert update["failure_mode"] == "FAILED_QV" and update["fail_reason"] == "leakage: LEAKS_ANSWER"
    assert update["history"][-1]["failure_mode"] == "FAILED_QV"


def test_failure_on_the_last_round_rejects_the_chunk_and_keeps_history():
    earlier = [{"round_num": 2, "question": "old", "failure_mode": "TOO_EASY", "fail_reason": "x"}]
    update = node_evaluate(judged([70, 70, 70], round_num=3, history=earlier))
    assert update["status"] == "REJECTED"
    assert [h["round_num"] for h in update["history"]] == [2, 3]


def test_infrastructure_error_rejects_the_chunk_without_feedback():
    update = node_evaluate(ready_state(error="judge: grading weak answers failed: timeout"))
    assert update == {"status": "REJECTED", "failure_mode": None,
                      "fail_reason": "error: judge: grading weak answers failed: timeout"}


@pytest.mark.parametrize("state", [ready_state(verifier_verdict="PASS"), judged([40, 40, 40])])
def test_missing_scores_are_treated_as_an_error(state):
    update = node_evaluate(state)
    assert update["status"] == "REJECTED" and update["fail_reason"].startswith("error:")


def test_a_zero_weak_attempt_is_too_hard_not_too_easy():
    update = node_evaluate(judged([28.8, 0.0, 25.0]))
    assert update["failure_mode"] == "TOO_HARD" and update["fail_reason"] == "a weak attempt scored 0"


def test_a_weak_attempt_above_75_still_counts_as_too_easy_even_with_a_zero():
    assert node_evaluate(judged([80, 0, 30]))["failure_mode"] == "TOO_EASY"
