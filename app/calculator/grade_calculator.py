from decimal import Decimal
from math import isfinite


class GradeCalculator:
    @staticmethod
    def grade_point(percentage):
        value = Decimal(str(percentage))
        if not value.is_finite() or not 0 <= value <= 100:
            raise ValueError('Percentage must be a finite number between 0 and 100.')
        for minimum, equivalent in [(97,1), (94,1.25), (91,1.5), (88,1.75),
                                    (85,2), (82,2.25), (79,2.5), (76,2.75), (75,3)]:
            if value >= minimum:
                return float(equivalent)
        return 5.0

    def calculate_breakdown(self, scores):
        if not scores:
            raise ValueError("No scores were provided.")

        categories = {}

        for score in scores:
            component_name = score[5]
            student_score = float(score[1])
            max_score = float(score[7])
            percentage_id = score[9]
            percentage = float(score[10])

            if not all(isfinite(v) for v in (student_score, max_score, percentage)):
                raise ValueError('Scores, maximums and weights must be finite numbers.')

            if max_score <= 0:
                raise ValueError(f"Invalid max score for {component_name}.")

            if student_score < 0 or student_score > max_score:
                raise ValueError(
                    f"Score for {component_name} must be between 0 and {max_score:.2f}."
                )

            if percentage <= 0 or percentage > 100:
                raise ValueError(
                    f"Invalid percentage for grading category {percentage_id}."
                )

            if percentage_id not in categories:
                categories[percentage_id] = {
                    "percentage": percentage,
                    "component_scores": []
                }

            category = categories[percentage_id]
            category["component_scores"].append({
                "component": component_name,
                "score": student_score,
                "max_score": max_score,
                "percentage_score": (student_score / max_score) * 100
            })

        total_weight = sum(
            category["percentage"] for category in categories.values()
        )

        if abs(total_weight - 100) > 0.001:
            raise ValueError(
                f"Grading percentages must total 100%. Current total: {total_weight:.2f}%."
            )

        final_grade = 0
        breakdown = []

        for percentage_id, category in categories.items():
            average = sum(
                item["percentage_score"]
                for item in category["component_scores"]
            ) / len(category["component_scores"])

            weighted = average * (category["percentage"] / 100)
            final_grade += weighted

            breakdown.append({
                "percentage_id": percentage_id,
                "weight": category["percentage"],
                "average": round(average, 2),
                "weighted_grade": round(weighted, 2),
                "components": category["component_scores"]
            })

        return {
            "final_grade": round(final_grade, 2),
            "total_weight": round(total_weight, 2),
            "categories": breakdown
        }

    def calculate(self, scores):
        return self.calculate_breakdown(scores)["final_grade"]
