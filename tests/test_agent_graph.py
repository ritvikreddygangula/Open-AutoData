import json

from src.agent_graph import build_graph, run_chunk
from src.default_prompts import DEFAULTS
from src.recorder import Recorder
from tests.fakes import RoutedClient, connection_error
from tests.samples import CHALLENGER, CHUNK, JUDGE, STRONG, WEAK, as_json, package

PASS_QV = {"leakage": "NO_LEAKAGE", "question_quality": "GOOD", "rubric_quality": "PASS",
           "type_consistency": "CONSISTENT", "feedback": ""}
FAIL_QV = {**PASS_QV, "leakage": "LEAKS_ANSWER", "feedback": "context gives the margin"}
CHUNK_ROW = {"chunk_id": "4", "text": CHUNK}


def models(verifier_replies, weak_met, strong_met, rounds=3):
    """Fake OpenRouter. Rubric is 10 criteria x weight 3, so meeting k criteria scores 10k."""
    verifier = list(verifier_replies)

    def nemotron(request):  # verifier and judge share this model
        if request["messages"][0]["content"] == DEFAULTS["VERIFIER_SYSTEM"]:
            return as_json(verifier.pop(0))
        met = strong_met if "strong answer" in request["messages"][1]["content"] else weak_met
        return json.dumps({"verdicts": [True] * met + [False] * (10 - met), "note": f"met {met}"})

    return RoutedClient({
        CHALLENGER: [as_json(package(question=f"Question {i}")) for i in range(1, rounds + 1)],
        JUDGE: nemotron,
        WEAK: lambda request: "weak answer",
        STRONG: lambda request: "strong answer",
    })


def run(tmp_path, client, fake_llm):
    fake_llm(client)
    recorder = Recorder(tmp_path / "trajectories.json", tmp_path / "accepted.json")
    final = run_chunk(build_graph(recorder), CHUNK_ROW, run_id="run-1")
    trajectories = json.loads((tmp_path / "trajectories.json").read_text())
    accepted_path = tmp_path / "accepted.json"
    accepted = json.loads(accepted_path.read_text()) if accepted_path.exists() else []
    return final, trajectories, accepted


def test_failed_quality_check_then_accepted_question(tmp_path, fake_llm):
    client = models([FAIL_QV, PASS_QV], weak_met=4, strong_met=9)
    final, trajectories, accepted = run(tmp_path, client, fake_llm)

    assert final["status"] == "ACCEPTED" and final["round_num"] == 2
    assert [(r["round_num"], r["status"], r["failure_mode"]) for r in trajectories] == [
        (1, "REVISE", "FAILED_QV"), (2, "ACCEPTED", None)]
    assert trajectories[1]["weak_score"] == 40.0 and trajectories[1]["strong_score"] == 90.0
    assert [r["question"] for r in accepted] == ["Question 2"]
    assert "context gives the margin" in client.calls_to(CHALLENGER)[1]["messages"][1]["content"]


def test_strong_solver_is_skipped_when_weak_does_too_well_and_chunk_stops_after_three_rounds(tmp_path, fake_llm):
    client = models([PASS_QV] * 3, weak_met=8, strong_met=9)
    final, trajectories, accepted = run(tmp_path, client, fake_llm)

    assert final["status"] == "REJECTED" and final["round_num"] == 3
    assert [r["failure_mode"] for r in trajectories] == ["TOO_EASY"] * 3
    assert client.calls_to(STRONG) == [] and accepted == []
    assert all(r["strong_answer"] == [] for r in trajectories)


def test_model_outage_ends_the_chunk_after_one_record(tmp_path, fake_llm):
    client = models([PASS_QV], weak_met=4, strong_met=9)
    client.routes[CHALLENGER] = lambda request: connection_error()
    final, trajectories, _ = run(tmp_path, client, fake_llm)

    assert final["status"] == "REJECTED" and final["fail_reason"].startswith("error: challenger")
    assert len(trajectories) == 1 and client.calls_to(JUDGE) == []
