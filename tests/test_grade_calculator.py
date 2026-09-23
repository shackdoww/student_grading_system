from app.calculator.grade_calculator import GradeCalculator


def test_grade_calculator():
    scores = [
        ("SC001", 18, "Good", None, "GC001", "Quiz 1", "Quiz", 20, "", "GP001", 30, "CO001", "Prelim", None, None),
        ("SC002", 45, "Good", None, "GC002", "Assignment 1", "Assignment", 50, "", "GP001", 30, "CO001", "Prelim", None, None),
        ("SC003", 42, "Good", None, "GC003", "Activity 1", "Activity", 50, "", "GP002", 40, "CO001", "Prelim", None, None),
        ("SC004", 85, "Passed", None, "GC004", "Prelim Exam", "Exam", 100, "", "GP003", 30, "CO001", "Prelim", None, None),
    ]

    calculator = GradeCalculator()

    assert calculator.calculate(scores) == 86.1
