import json

from src.default_prompts import DEFAULTS
from src.nodes import node_judge
from tests.fakes import RoutedClient, connection_error
from tests.samples import JUDGE, package, ready_state

ANSWERS = ["answer one", "answer two", "answer three"]
MET = {"answer one": 10, "answer two": 5, "answer three": 1}  # criteria met (rubric: 10 x weight 3)


def grade_by_answer(request):
    answer = request["messages"][1]["content"].split("<response>\n", 1)[1].split("\n</response>")[0]
    met = MET[answer]
    return json.dumps({"verdicts": [True] * met + [False] * (10 - met), "note": f"{answer} note"})


def test_each_answer_is_graded_separately_and_scores_stay_in_order(fake_llm):
    client = fake_llm(RoutedClient({JUDGE: grade_by_answer}))
    update = node_judge(ready_state(weak_answers=ANSWERS), "weak")

    assert update["weak_attempt_scores"] == [100.0, 50.0, 10.0]
    assert update["weak_score"] == 53.3
    assert update["judge_feedback"] == "weak 1: answer one note\nweak 2: answer two note\nweak 3: answer three note"
    assert len(client.calls) == 3


def test_judge_sees_question_numbered_rubric_and_answer_but_not_the_reference(fake_llm):
    client = fake_llm(RoutedClient({JUDGE: grade_by_answer}))
    node_judge(ready_state(weak_answers=ANSWERS), "weak")

    call = client.calls[0]
    assert call["temperature"] == 0
    assert call["messages"][0]["content"] == DEFAULTS["JUDGE_SYSTEM"]
    user = call["messages"][1]["content"]
    assert user.startswith(f"QUESTION:\n{package()['question']}\n\nRUBRIC:\n1. Computes step 0\n2. Computes step 1\n")
    assert package()["reference_answer"] not in user


def test_strong_feedback_is_added_after_the_weak_feedback(fake_llm):
    fake_llm(RoutedClient({JUDGE: grade_by_answer}))
    state = ready_state(strong_answers=ANSWERS, judge_feedback="weak 1: earlier")
    update = node_judge(state, "strong")
    assert update["strong_score"] == 53.3
    assert update["judge_feedback"].startswith("weak 1: earlier\nstrong 1: answer one note")


def test_verdict_list_of_the_wrong_length_is_an_error(fake_llm):
    fake_llm(RoutedClient({JUDGE: lambda request: json.dumps({"verdicts": [True] * 9, "note": ""})}))
    update = node_judge(ready_state(weak_answers=ANSWERS), "weak")
    assert update["error"].startswith("judge:") and "weak" in update["error"]


def test_judge_outage_is_an_error(fake_llm):
    fake_llm(RoutedClient({JUDGE: lambda request: connection_error()}))
    assert node_judge(ready_state(weak_answers=ANSWERS), "weak")["error"].startswith("judge:")
