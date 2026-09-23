class GradeCalculator:

    def calculate(self, scores):
        category_totals = {}

        for score in scores:
            component_name = score[5]
            max_score = float(score[7])
            student_score = float(score[1])
            percentage_id = score[9]
            percentage = float(score[10])

            if max_score <= 0:
                raise ValueError(
                    f"Invalid max score for {component_name}"
                )

            component_percentage = (student_score / max_score) * 100

            if percentage_id not in category_totals:
                category_totals[percentage_id] = {
                    "percentage": percentage,
                    "scores": []
                }

            category_totals[percentage_id]["scores"].append(
                component_percentage
            )

        final_grade = 0

        for category in category_totals.values():
            category_average = sum(category["scores"]) / len(category["scores"])
            weighted_grade = category_average * (category["percentage"] / 100)

            final_grade += weighted_grade

        return round(final_grade, 2)