import pytest

from src.rubric import parse_verdicts, score_answer, validate_rubric


def rubric_items(n, weight=3):
    return [{"criterion": f"Point {i}", "weight": weight} for i in range(n)]


def test_validate_accepts_ten_to_fifteen_positive_criteria():
    assert validate_rubric(rubric_items(10)) == rubric_items(10)
    assert validate_rubric(rubric_items(15)) == rubric_items(15)


@pytest.mark.parametrize("n", [0, 9, 16])
def test_validate_rejects_wrong_criterion_count(n):
    assert validate_rubric(rubric_items(n)) is None


def test_validate_coerces_digit_string_weights_and_trims_text():
    raw = rubric_items(9) + [{"criterion": "  Names the driver  ", "weight": "7"}]
    assert validate_rubric(raw)[-1] == {"criterion": "Names the driver", "weight": 7}


@pytest.mark.parametrize("weight", [0, 8, -2, "+5", 2.5, True, None, "high"])
def test_validate_rejects_weights_outside_one_to_seven_integers(weight):
    assert validate_rubric(rubric_items(9) + [{"criterion": "x", "weight": weight}]) is None


@pytest.mark.parametrize("bad", [{"criterion": "", "weight": 3}, {"weight": 3}, "just text"])
def test_validate_rejects_malformed_items(bad):
    assert validate_rubric(rubric_items(9) + [bad]) is None


def test_validate_rejects_non_list():
    assert validate_rubric({"criterion": "x", "weight": 1}) is None


def test_parse_verdicts_accepts_common_yes_no_forms():
    assert parse_verdicts([True, "yes", 1, "TRUE", False, "no", 0, "false"], 8) == [
        True, True, True, True, False, False, False, False,
    ]


@pytest.mark.parametrize("raw", [[True, False], [True, False, True, True], "yes", [True, "maybe", False]])
def test_parse_verdicts_rejects_wrong_length_or_unknown_values(raw):
    assert parse_verdicts(raw, 3) is None


def test_score_is_met_weight_over_total_weight():
    rubric = [{"criterion": "a", "weight": 7}, {"criterion": "b", "weight": 2}, {"criterion": "c", "weight": 1}]
    assert score_answer(rubric, [True, False, True]) == 80.0
    assert score_answer(rubric, [False, True, False]) == 20.0


def test_score_rounds_to_one_decimal():
    rubric = [{"criterion": "a", "weight": 1}] * 3
    assert score_answer(rubric, [True, False, False]) == 33.3
