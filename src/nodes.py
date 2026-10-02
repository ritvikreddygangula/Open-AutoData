"""The Agentic Self-Instruct agents (Autodata paper §3.1) as LangGraph nodes.

Each node takes the state and returns only the fields it changes.
"""
import json

from src import config, llm
from src.default_prompts import get_prompt
from src.rubric import validate_rubric

CHALLENGER_TEMPERATURE = 0.7

# Everything a round produces; each new question starts from a clean slate.
_FRESH_ROUND = {
    "verifier_verdict": None,
    "verifier_feedback": None,
    "weak_answers": [],
    "strong_answers": [],
    "weak_attempt_scores": [],
    "strong_attempt_scores": [],
    "weak_score": None,
    "strong_score": None,
    "score_gap": None,
    "judge_feedback": None,
    "failure_mode": None,
    "fail_reason": None,
    "status": "PENDING",
    "error": None,
}

# How the challenger sees earlier failures (paper Fig. 7, "Calling the challenger").
_FAILURE_GROUPS = (
    ("TOO_EASY", "TOO EASY (the weak solver scored too high)"),
    ("FAILED_ON_STRONG", "FAILED ON STRONG (the strong solver scored too low or the gap was too small)"),
    ("FAILED_QV", "FAILED QUALITY CHECK"),
)
_TEXT_FIELDS = ("question_type", "context", "question", "reference_answer")


def _system(name: str) -> dict:
    return {"role": "system", "content": get_prompt(name)}


def _filing(state) -> str:
    return f"<filing>\n{state['chunk_text']}\n</filing>"


def _challenger_request(state) -> str:
    parts = [_filing(state), "Generate a challenging question-answer pair with a grading rubric from this filing excerpt."]
    history = state.get("history") or []
    if history:
        parts.append("These earlier questions did not meet the acceptance criteria:")
        for mode, title in _FAILURE_GROUPS:
            lines = [
                f'- Round {h["round_num"]}: "{h["question"]}" ({h["fail_reason"]})'
                for h in history
                if h["failure_mode"] == mode
            ]
            if lines:
                parts.append(f"{title}:\n" + "\n".join(lines))
        parts.append(
            "Write an ENTIRELY NEW question from a DIFFERENT angle that requires deeper reasoning. "
            "Do not rephrase any earlier question."
        )
    return "\n\n".join(parts)


def _check_package(reply: dict | None) -> tuple[dict | None, str]:
    """Return the cleaned challenger package, or None and what was wrong with it."""
    if reply is None:
        return None, "no usable JSON reply"
    problems = [
        f'"{field}" must be non-empty text'
        for field in _TEXT_FIELDS
        if not isinstance(reply.get(field), str) or not reply[field].strip()
    ]
    tags = reply.get("skill_tags")
    if not isinstance(tags, list) or not tags or not all(isinstance(t, str) and t.strip() for t in tags):
        problems.append('"skill_tags" must be a list of 2-3 snake_case strings')
    rubric = validate_rubric(reply.get("rubric"))
    if rubric is None:
        problems.append(
            f'"rubric" must have {config.RUBRIC_MIN_ITEMS}-{config.RUBRIC_MAX_ITEMS} items, each '
            f'{{"criterion": text, "weight": whole number 1-{config.RUBRIC_MAX_WEIGHT}}}'
        )
    if problems:
        return None, "; ".join(problems)
    package = {field: reply[field].strip() for field in _TEXT_FIELDS}
    return {**package, "skill_tags": [t.strip() for t in tags], "rubric": rubric}, ""


def node_challenger(state) -> dict:
    """Write a new context, question, reference answer and rubric from the filing chunk."""
    update = {**_FRESH_ROUND, "round_num": state["round_num"] + 1}
    messages = [_system("CHALLENGER_SYSTEM"), {"role": "user", "content": _challenger_request(state)}]
    try:
        reply = llm.chat_json("challenger", messages, CHALLENGER_TEMPERATURE)
        package, problem = _check_package(reply)
        if package is None and reply is not None:
            # One correction round for a parseable reply that broke the rules.
            messages += [
                {"role": "assistant", "content": json.dumps(reply)},
                {"role": "user", "content": f"Your reply broke these rules: {problem}. "
                                            "Reply again with one corrected JSON object."},
            ]
            package, problem = _check_package(llm.chat_json("challenger", messages, CHALLENGER_TEMPERATURE))
    except llm.LLMError as e:
        return {**update, "error": f"challenger: {e}"}
    if package is None:
        return {**update, "error": f"challenger: {problem}"}
    return {**update, **package}
