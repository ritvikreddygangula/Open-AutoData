"""Rubric checks and scoring: the judge says met/not met, code does the math."""
from src import config

_TRUE = {"true", "yes", "1", "met"}
_FALSE = {"false", "no", "0", "not met"}


def _weight(value) -> int | None:
    # Strict on purpose: the paper saw "+8"-style weights break scoring (§4).
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        weight = value
    elif isinstance(value, str) and value.strip().isdigit():
        weight = int(value)
    else:
        return None
    return weight if 1 <= weight <= config.RUBRIC_MAX_WEIGHT else None


def validate_rubric(raw) -> list[dict] | None:
    """Return a clean rubric, or None if the challenger's rubric breaks the paper's rules."""
    if not isinstance(raw, list) or not config.RUBRIC_MIN_ITEMS <= len(raw) <= config.RUBRIC_MAX_ITEMS:
        return None
    rubric = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        criterion = item.get("criterion")
        weight = _weight(item.get("weight"))
        if not isinstance(criterion, str) or not criterion.strip() or weight is None:
            return None
        rubric.append({"criterion": criterion.strip(), "weight": weight})
    return rubric


def _verdict(value) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return None


def parse_verdicts(raw, n: int) -> list[bool] | None:
    """Return one met/not-met verdict per rubric criterion, or None if the judge's list is unusable."""
    if not isinstance(raw, list) or len(raw) != n:
        return None
    verdicts = [_verdict(v) for v in raw]
    return None if None in verdicts else verdicts


def score_answer(rubric: list[dict], verdicts: list[bool]) -> float:
    total = sum(item["weight"] for item in rubric)
    met = sum(item["weight"] for item, ok in zip(rubric, verdicts) if ok)
    return round(100 * met / total, 1)
