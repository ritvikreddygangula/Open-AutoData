"""LangGraph state for one chunk, and the shared JSON record (sql/schema.sql)."""
from datetime import datetime, timezone
from typing import Literal, TypedDict

Status = Literal["PENDING", "REVISE", "ACCEPTED", "REJECTED"]
Arm = Literal["loop", "baseline"]
# Why a round failed, in the paper's groups (Fig. 7): fed back to the challenger next round.
FailureMode = Literal["TOO_EASY", "FAILED_ON_STRONG", "FAILED_QV"]


class AgentState(TypedDict, total=False):
    run_id: str
    arm: Arm
    chunk_id: str
    chunk_text: str
    round_num: int
    # Challenger output (paper §3.1): solvers see only context + question.
    question_type: str
    skill_tags: list[str]
    context: str
    question: str
    reference_answer: str
    rubric: list[dict]
    verifier_verdict: Literal["PASS", "FAIL"]
    verifier_feedback: str
    weak_answers: list[str]
    strong_answers: list[str]
    weak_attempt_scores: list[float]
    strong_attempt_scores: list[float]
    weak_score: float
    strong_score: float
    score_gap: float
    judge_feedback: str
    status: Status
    failure_mode: FailureMode
    fail_reason: str
    # Earlier failed rounds for this chunk, shown to the challenger.
    history: list[dict]
    # Infrastructure failure (model down, unusable reply); ends the chunk.
    error: str


# Column order follows sql/schema.sql.
RECORD_FIELDS = (
    "run_id", "arm", "chunk_id", "round_num", "question", "reference_answer",
    "weak_answer", "strong_answer",
    "weak_score", "strong_score", "score_gap", "judge_feedback", "status",
    # Not schema columns yet; Snowflake keeps them in RAW.
    "question_type", "skill_tags", "context", "rubric",
    "weak_attempt_scores", "strong_attempt_scores",
    "verifier_feedback", "failure_mode", "fail_reason", "timestamp",
)
# The schema's answer columns are singular; each holds all SOLVER_SAMPLES answers as a list.
_STATE_KEY = {"weak_answer": "weak_answers", "strong_answer": "strong_answers"}


def initial_state(chunk_id: str, chunk_text: str, run_id: str, arm: Arm = "loop") -> AgentState:
    return {
        "run_id": run_id,
        "arm": arm,
        "chunk_id": chunk_id,
        "chunk_text": chunk_text,
        "round_num": 0,
        "weak_answers": [],
        "strong_answers": [],
        "weak_attempt_scores": [],
        "strong_attempt_scores": [],
        "history": [],
        "status": "PENDING",
    }


def to_record(state: AgentState) -> dict:
    record = {field: state.get(_STATE_KEY.get(field, field)) for field in RECORD_FIELDS}
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    return record
