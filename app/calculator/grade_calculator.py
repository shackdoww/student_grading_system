"""The central rubric grade-point scale, applied before percentage rounding."""

from decimal import Decimal, InvalidOperation


class GradeCalculator:
    @staticmethod
    def grade_point(percentage):
        try:
            value = Decimal(str(percentage))
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError("Enter a finite percentage between 0 and 100.") from error
        if not value.is_finite() or not 0 <= value <= 100:
            raise ValueError("Percentage must be a finite number between 0 and 100.")
        for minimum, equivalent in [
            (97, 1),
            (94, 1.25),
            (91, 1.5),
            (88, 1.75),
            (85, 2),
            (82, 2.25),
            (79, 2.5),
            (76, 2.75),
            (75, 3),
        ]:
            if value >= minimum:
                return float(equivalent)
        return 5.0
