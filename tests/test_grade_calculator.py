import pytest

from app.calculator.grade_calculator import GradeCalculator


def make_scores():
    return [
        ("SC001", 18, "Good", None, "GC001", "Quiz 1", "Quiz", 20, "", "GP001", 30, "CO001", "Prelim", None, None),
        ("SC002", 45, "Good", None, "GC002", "Assignment 1", "Assignment", 50, "", "GP001", 30, "CO001", "Prelim", None, None),
        ("SC003", 42, "Good", None, "GC003", "Activity 1", "Activity", 50, "", "GP002", 40, "CO001", "Prelim", None, None),
        ("SC004", 85, "Passed", None, "GC004", "Prelim Exam", "Exam", 100, "", "GP003", 30, "CO001", "Prelim", None, None),
    ]


def test_grade_calculator():
    assert GradeCalculator().calculate(make_scores()) == 86.1


def test_grade_breakdown():
    result = GradeCalculator().calculate_breakdown(make_scores())

    assert result["final_grade"] == 86.1
    assert result["total_weight"] == 100.0
    assert result["categories"][0]["average"] == 90.0
    assert result["categories"][0]["weighted_grade"] == 27.0


def test_empty_scores_are_rejected():
    with pytest.raises(ValueError, match="No scores"):
        GradeCalculator().calculate([])


def test_score_above_maximum_is_rejected():
    scores = make_scores()
    scores[0] = (
        "SC001", 21, "Invalid", None, "GC001", "Quiz 1",
        "Quiz", 20, "", "GP001", 30, "CO001", "Prelim", None, None
    )

    with pytest.raises(ValueError, match="between 0 and 20"):
        GradeCalculator().calculate(scores)


def test_negative_score_is_rejected():
    scores = make_scores()
    scores[0] = (
        "SC001", -1, "Invalid", None, "GC001", "Quiz 1",
        "Quiz", 20, "", "GP001", 30, "CO001", "Prelim", None, None
    )

    with pytest.raises(ValueError, match="between 0 and 20"):
        GradeCalculator().calculate(scores)


def test_weights_must_total_100():
    scores = make_scores()
    scores[0] = (
        "SC001", 18, "Good", None, "GC001", "Quiz 1",
        "Quiz", 20, "", "GP001", 20, "CO001", "Prelim", None, None
    )

    with pytest.raises(ValueError, match="total 100"):
        GradeCalculator().calculate(scores)
