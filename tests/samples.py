"""Ready-made agent outputs for node tests."""
import json

from src.state import initial_state

CHALLENGER = "z-ai/glm-5.3"
VERIFIER = "nvidia/nemotron-3-super-120b-a12b"
JUDGE = "nvidia/nemotron-3-super-120b-a12b"
WEAK = "meta-llama/llama-3.2-3b-instruct"
STRONG = "deepseek/deepseek-v4.1-flash"

CHUNK = "Net sales were $66,533 thousand in Q1 2026 versus $59,002 thousand in Q1 2025."


def rubric(n=10, weight=3):
    return [{"criterion": f"Computes step {i}", "weight": weight} for i in range(n)]


def package(**overrides):
    data = {
        "question_type": "margin driver decomposition",
        "skill_tags": ["multi_step_calculation", "causal_reasoning"],
        "context": "Net sales rose from $59.0M to $66.5M while cost of goods sold rose from $48.0M to $55.5M.",
        "question": "Did gross margin improve, and what drove the change?",
        "reference_answer": "Gross margin fell from 18.6% to 16.6% because costs grew faster than sales.",
        "rubric": rubric(),
    }
    data.update(overrides)
    return data


def as_json(data):
    return json.dumps(data)


def chunk_state(**overrides):
    return {**initial_state("4", CHUNK, run_id="run-1"), **overrides}


def ready_state(**overrides):
    """State right after the challenger wrote a package."""
    return chunk_state(**{"round_num": 1, **package(), **overrides})
