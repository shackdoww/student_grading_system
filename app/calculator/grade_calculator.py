class GradeCalculator:

    def calculate(self, scores):
        if not scores:
            raise ValueError("No scores were provided.")

        category_totals = {}

        for score in scores:
            component_name = score[5]
            student_score = float(score[1])
            max_score = float(score[7])
            percentage_id = score[9]
            percentage = float(score[10])

            if max_score <= 0:
                raise ValueError(f"Invalid max score for {component_name}.")

            if student_score < 0:
                raise ValueError(f"Score cannot be negative for {component_name}.")

            if student_score > max_score:
                raise ValueError(
                    f"Score for {component_name} cannot exceed {max_score}."
                )

            if percentage <= 0 or percentage > 100:
                raise ValueError(
                    f"Invalid percentage for grading category {percentage_id}."
                )

            if percentage_id not in category_totals:
                category_totals[percentage_id] = {
                    "percentage": percentage,
                    "scores": []
                }

            category_totals[percentage_id]["scores"].append(
                (student_score / max_score) * 100
            )

        total_weight = sum(
            category["percentage"]
            for category in category_totals.values()
        )

        if total_weight <= 0:
            raise ValueError("No valid grading percentage was found.")

        final_grade = 0

        for category in category_totals.values():
            category_average = (
                sum(category["scores"]) / len(category["scores"])
            )
            weighted_grade = (
                category_average * (category["percentage"] / 100)
            )
            final_grade += weighted_grade

        return round(final_grade, 2)
