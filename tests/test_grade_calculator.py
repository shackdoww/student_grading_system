from decimal import Decimal
import pytest
from app.calculator.grade_calculator import GradeCalculator


@pytest.mark.parametrize("bad", [-1, 101, "NaN", "Infinity", "", None])
def test_invalid_percentages_have_validation_errors(bad):
    with pytest.raises(ValueError):
        GradeCalculator.grade_point(bad)


def test_unrounded_failure_boundary():
    assert GradeCalculator.grade_point(Decimal("74.999")) == 5
    assert GradeCalculator.grade_point(Decimal("75")) == 3
