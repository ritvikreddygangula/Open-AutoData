"""The paper's acceptance gate (Fig. 7), split so the graph can stop after the weak check."""
from src import config

# A zero means the question was too hard for the weak solver (no learning signal), not too easy.
WEAK_ZERO = "a weak attempt scored 0"


def average(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 1)


def weak_gate_failures(weak_scores: list[float]) -> list[str]:
    """Reasons the weak solver did too well; empty means the question is hard enough."""
    failures = []
    weak = average(weak_scores)
    if weak > config.WEAK_MAX:
        failures.append(f"weak_score {weak} > {config.WEAK_MAX}")
    if max(weak_scores) > config.WEAK_ATTEMPT_MAX:
        failures.append(f"best weak attempt {max(weak_scores):g} > {config.WEAK_ATTEMPT_MAX}")
    if min(weak_scores) == 0:
        failures.append(WEAK_ZERO)
    return failures


def strong_gate_failures(weak_score: float, strong_scores: list[float]) -> list[str]:
    """Reasons the strong solver did not separate from the weak one; empty means accept."""
    failures = []
    strong = average(strong_scores)
    if strong < config.STRONG_MIN:
        failures.append(f"strong_score {strong} < {config.STRONG_MIN}")
    if strong >= config.STRONG_MAX:
        failures.append(f"strong_score {strong} >= {config.STRONG_MAX}")
    gap = round(strong - weak_score, 1)
    if gap < config.GAP_MIN:
        failures.append(f"score_gap {gap} < {config.GAP_MIN}")
    return failures
