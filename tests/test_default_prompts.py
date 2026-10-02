import sys
import types

import pytest

from src.default_prompts import DEFAULTS, get_prompt

NAMES = ("CHALLENGER_SYSTEM", "VERIFIER_SYSTEM", "SOLVER_SYSTEM", "JUDGE_SYSTEM")


def test_every_agent_has_a_default_prompt():
    assert set(DEFAULTS) == set(NAMES)
    assert all(DEFAULTS[name].strip() for name in NAMES)


def test_defaults_are_used_when_person_three_prompts_are_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "src.prompts", None)
    assert get_prompt("JUDGE_SYSTEM") == DEFAULTS["JUDGE_SYSTEM"]


def test_person_three_prompts_override_defaults(monkeypatch):
    custom = types.ModuleType("src.prompts")
    custom.JUDGE_SYSTEM = "custom judge"
    custom.SOLVER_SYSTEM = "   "
    monkeypatch.setitem(sys.modules, "src.prompts", custom)
    assert get_prompt("JUDGE_SYSTEM") == "custom judge"
    assert get_prompt("SOLVER_SYSTEM") == DEFAULTS["SOLVER_SYSTEM"]
    assert get_prompt("CHALLENGER_SYSTEM") == DEFAULTS["CHALLENGER_SYSTEM"]


def test_unknown_prompt_name_is_an_error():
    with pytest.raises(KeyError):
        get_prompt("REVISION_SYSTEM")


def test_challenger_prompt_names_every_output_field():
    for field in ("question_type", "skill_tags", "context", "question", "reference_answer", "rubric"):
        assert f'"{field}"' in DEFAULTS["CHALLENGER_SYSTEM"]


def test_solver_prompt_never_hints_at_strength():
    text = DEFAULTS["SOLVER_SYSTEM"].lower()
    assert "weak" not in text and "strong" not in text


def test_numeric_rubric_criteria_must_state_the_expected_value():
    assert "state the expected value" in DEFAULTS["CHALLENGER_SYSTEM"]
    assert "does not state the expected value" in DEFAULTS["VERIFIER_SYSTEM"]
