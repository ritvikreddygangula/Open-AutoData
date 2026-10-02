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
        "verifier": "nvidia/nemotron-3-super-120b-a12b",
    }


def test_paper_acceptance_limits():
    assert (config.WEAK_ATTEMPT_MAX, config.STRONG_MAX) == (75, 95)
    assert (config.RUBRIC_MIN_ITEMS, config.RUBRIC_MAX_ITEMS, config.RUBRIC_MAX_WEIGHT) == (10, 15, 7)


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
