import itertools

import pytest

from src.nodes import node_solvers
from tests.fakes import RoutedClient, connection_error
from tests.samples import CHUNK, STRONG, WEAK, package, ready_state


def numbered(prefix):
    counter = itertools.count(1)
    return lambda request: f"{prefix} answer {next(counter)}"


def test_weak_solver_answers_three_times_from_context_and_question_only(fake_llm):
    client = fake_llm(RoutedClient({WEAK: numbered("weak")}))
    update = node_solvers(ready_state(), "weak")

    assert sorted(update["weak_answers"]) == ["weak answer 1", "weak answer 2", "weak answer 3"]
    calls = client.calls_to(WEAK)
    assert len(calls) == 3 and all(call["temperature"] == 1.0 for call in calls)
    user = calls[0]["messages"][1]["content"]
    assert user == f"CONTEXT:\n{package()['context']}\n\nQUESTION:\n{package()['question']}"
    assert CHUNK not in user and package()["reference_answer"] not in user


def test_strong_solver_gets_exactly_the_weak_solvers_prompt(fake_llm):
    client = fake_llm(RoutedClient({WEAK: numbered("weak"), STRONG: numbered("strong")}))
    node_solvers(ready_state(), "weak")
    update = node_solvers(ready_state(), "strong")

    assert len(update["strong_answers"]) == 3
    assert client.calls_to(STRONG)[0]["messages"] == client.calls_to(WEAK)[0]["messages"]


def test_solver_outage_is_an_error(fake_llm):
    fake_llm(RoutedClient({WEAK: lambda request: connection_error()}))
    update = node_solvers(ready_state(), "weak")
    assert update == {"error": update["error"]}
    assert update["error"].startswith("solver: weak")


def test_unknown_solver_role_is_rejected():
    with pytest.raises(ValueError):
        node_solvers(ready_state(), "judge")
