from src.gate import average, strong_gate_failures, weak_gate_failures


def test_average_rounds_to_one_decimal():
    assert average([10, 20, 40]) == 23.3


def test_weak_gate_passes_at_the_boundaries():
    assert weak_gate_failures([65, 75, 55]) == []


def test_weak_gate_fails_when_average_is_too_high():
    assert weak_gate_failures([70, 70, 70]) == ["weak_score 70.0 > 65"]


def test_weak_gate_fails_when_one_attempt_is_too_good():
    assert weak_gate_failures([76, 40, 40]) == ["best weak attempt 76 > 75"]


def test_weak_gate_fails_on_a_zero_attempt():
    assert weak_gate_failures([0, 50, 50]) == ["a weak attempt scored 0"]


def test_strong_gate_passes_at_the_boundaries():
    assert strong_gate_failures(40.0, [60, 60, 60]) == []
    assert strong_gate_failures(10.0, [94.9, 94.9, 94.9]) == []


def test_strong_gate_reports_every_failed_check():
    assert strong_gate_failures(50.0, [55, 55, 55]) == ["strong_score 55.0 < 60", "score_gap 5.0 < 20"]


def test_strong_gate_fails_when_strong_saturates():
    assert strong_gate_failures(30.0, [95, 95, 95]) == ["strong_score 95.0 >= 95"]
