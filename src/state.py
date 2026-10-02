"""LangGraph state for one chunk, and the shared JSON record (MASTER_SPEC §4)."""
from datetime import datetime, timezone
from typing import Literal, TypedDict

Status = Literal["PENDING", "REVISE", "ACCEPTED", "REJECTED"]
Arm = Literal["loop", "baseline"]


class AgentState(TypedDict, total=False):
    run_id: str
    arm: Arm
    chunk_id: str
    chunk_text: str
    round_num: int
    question: str
    reference_answer: str
    weak_answers: list[str]
    strong_answers: list[str]
    weak_score: float
    strong_score: float
    score_gap: float
    judge_feedback: str
    status: Status
    fail_reason: str


# Column order follows sql/schema.sql.
RECORD_FIELDS = (
    "run_id", "arm",
    "chunk_id", "round_num", "question", "reference_answer",
    "weak_score", "strong_score", "score_gap", "judge_feedback", "status",
    "fail_reason", "timestamp",
)


def initial_state(chunk_id: str, chunk_text: str, run_id: str, arm: Arm = "loop") -> AgentState:
    return {
        "run_id": run_id,
        "arm": arm,
        "chunk_id": chunk_id,
        "chunk_text": chunk_text,
        "round_num": 0,
        "weak_answers": [],
        "strong_answers": [],
        "status": "PENDING",
    }


def to_record(state: AgentState) -> dict:
    record = {field: state.get(field) for field in RECORD_FIELDS}
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    return record
