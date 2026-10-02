"""The Agentic Self-Instruct agents (Autodata paper §3.1) as LangGraph nodes.

Each node takes the state and returns only the fields it changes.
"""
import json
from concurrent.futures import ThreadPoolExecutor

from src import config, llm
from src.default_prompts import get_prompt
from src.gate import average
from src.rubric import parse_verdicts, score_answer, validate_rubric

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


# Each check and the one value that means it passed (paper Fig. 9).
_VERIFIER_CHECKS = {
    "leakage": ("NO_LEAKAGE", {"NO_LEAKAGE", "LEAKS_ANSWER"}),
    "question_quality": ("GOOD", {"GOOD", "TOO_EASY", "RECALL"}),
    "rubric_quality": ("PASS", {"PASS", "FAIL"}),
    "type_consistency": ("CONSISTENT", {"CONSISTENT", "INCONSISTENT"}),
}


def node_verifier(state) -> dict:
    """Check the package for answer leakage, recall-only questions and a weak rubric before any solving."""
    sent = {field: state[field] for field in ("question_type", "context", "question", "rubric")}
    request = f"{_filing(state)}\n\nPACKAGE:\n{json.dumps(sent, indent=2)}"
    try:
        reply = llm.chat_json("verifier", [_system("VERIFIER_SYSTEM"), {"role": "user", "content": request}], 0)
    except llm.LLMError as e:
        return {"error": f"verifier: {e}"}
    if reply is None:
        return {"error": "verifier: no usable JSON reply"}

    failed = []
    for check, (good, allowed) in _VERIFIER_CHECKS.items():
        value = str(reply.get(check, "")).strip().upper()
        if value not in allowed:
            return {"error": f"verifier: unrecognised {check} value {reply.get(check)!r}"}
        if value != good:
            failed.append(f"{check}: {value}")
    feedback = str(reply.get("feedback") or "").strip()
    if not failed:
        return {"verifier_verdict": "PASS", "verifier_feedback": feedback}
    return {"verifier_verdict": "FAIL", "verifier_feedback": "; ".join(failed) + (f": {feedback}" if feedback else "")}


SOLVER_TEMPERATURE = 1.0  # paper §4: solvers sample at temperature 1.0
_SOLVER_ROLES = ("weak", "strong")


def _solver_request(state) -> str:
    # Solvers never see the filing or the reference answer (paper §3.1).
    return f"CONTEXT:\n{state['context']}\n\nQUESTION:\n{state['question']}"


def node_solvers(state, role: str) -> dict:
    """Answer the question SOLVER_SAMPLES times in parallel with the weak or strong model."""
    if role not in _SOLVER_ROLES:
        raise ValueError(f"unknown solver role {role!r}")
    # Identical prompt for both solvers: the paper saw agents "cheat" by telling the weak one to be weak.
    messages = [_system("SOLVER_SYSTEM"), {"role": "user", "content": _solver_request(state)}]
    try:
        with ThreadPoolExecutor(max_workers=config.SOLVER_SAMPLES) as pool:
            answers = list(pool.map(
                lambda _: llm.chat(role, messages, SOLVER_TEMPERATURE), range(config.SOLVER_SAMPLES)
            ))
    except llm.LLMError as e:
        return {"error": f"solver: {role} failed: {e}"}
    return {f"{role}_answers": answers}


class _UnusableGrade(Exception):
    pass


def _judge_request(state, answer: str) -> str:
    criteria = "\n".join(f"{i}. {item['criterion']}" for i, item in enumerate(state["rubric"], 1))
    return f"QUESTION:\n{state['question']}\n\nRUBRIC:\n{criteria}\n\nRESPONSE:\n<response>\n{answer}\n</response>"


def _grade(state, answer: str) -> tuple[float, str]:
    messages = [_system("JUDGE_SYSTEM"), {"role": "user", "content": _judge_request(state, answer)}]
    reply = llm.chat_json("judge", messages, 0)
    verdicts = parse_verdicts(reply.get("verdicts"), len(state["rubric"])) if reply else None
    if verdicts is None:
        raise _UnusableGrade("no usable verdict list")
    return score_answer(state["rubric"], verdicts), str(reply.get("note") or "").strip()


def node_judge(state, role: str) -> dict:
    """Grade each of one solver's answers against the rubric; code turns verdicts into 0-100 scores."""
    if role not in _SOLVER_ROLES:
        raise ValueError(f"unknown solver role {role!r}")
    answers = state[f"{role}_answers"]
    try:
        with ThreadPoolExecutor(max_workers=len(answers)) as pool:
            grades = list(pool.map(lambda answer: _grade(state, answer), answers))
    except (llm.LLMError, _UnusableGrade) as e:
        return {"error": f"judge: grading {role} answers failed: {e}"}

    scores = [score for score, _ in grades]
    notes = [f"{role} {i}: {note}" for i, (_, note) in enumerate(grades, 1)]
    feedback = "\n".join(filter(None, [state.get("judge_feedback"), *notes]))
    return {f"{role}_attempt_scores": scores, f"{role}_score": average(scores), "judge_feedback": feedback}
