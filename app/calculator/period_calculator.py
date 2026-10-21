"""Configurable component weights; grade points use unrounded Decimal percentages."""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from app.calculator.grade_calculator import GradeCalculator


def number(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(
            "Enter a number for every score and weight; blank values are not allowed."
        ) from error
    if not result.is_finite():
        raise ValueError("Grades and weights must be finite numbers.")
    return result


def rounded(value):
    return float(value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


class PeriodCalculator:
    def validate_policy(self, policy, weights, components):
        if not policy:
            raise ValueError("Configure period grading for this class first.")
        periods = [policy["midterm_period_id"], policy["final_period_id"]]
        if not all(periods) or periods[0] == periods[1]:
            raise ValueError("Midterm and Final must use distinct periods.")
        totals = [number(policy["midterm_weight"]), number(policy["final_weight"])]
        if any(w <= 0 for w in totals) or sum(totals) != 100:
            raise ValueError("Overall period weights must be positive and total 100%.")
        by_id = {c["component_id"]: c for c in components}
        if len({w["component_id"] for w in weights}) != len(weights):
            raise ValueError("Duplicate component weights are not allowed.")
        if any(w["component_id"] not in by_id for w in weights):
            raise ValueError("Every weight must reference an existing component.")
        if any(by_id[w["component_id"]]["period_id"] not in periods for w in weights):
            raise ValueError("Components must belong to the selected periods.")
        for period in periods:
            selected = [
                w for w in weights if by_id[w["component_id"]]["period_id"] == period
            ]
            if (
                not selected
                or any(number(w["percentage"]) <= 0 for w in selected)
                or sum(number(w["percentage"]) for w in selected) != 100
            ):
                raise ValueError(
                    "Component weights must be positive and total 100% in each period."
                )

    def calculate(
        self,
        policy,
        weights,
        components,
        scores,
        include_equivalents=False,
        period=None,
    ):
        self.validate_policy(policy, weights, components)
        if period not in (None, "midterm"):
            raise ValueError("Choose Midterm or the complete grade calculation.")
        actual = {s["component_id"]: s for s in scores}
        by_id = {c["component_id"]: c for c in components}
        results = {}
        for key, pid in [
            ("midterm", policy["midterm_period_id"]),
            ("final", policy["final_period_id"]),
        ]:
            if period == "midterm" and key == "final":
                continue
            value = Decimal(0)
            for weight in weights:
                component = by_id[weight["component_id"]]
                if component["period_id"] != pid:
                    continue
                if component["component_id"] not in actual:
                    raise ValueError(
                        f"Missing score: {component['name']}. Enter zero explicitly for a zero score."
                    )
                score = number(actual[component["component_id"]]["score"])
                maximum = number(component["max_score"])
                if maximum <= 0 or score < 0 or score > maximum:
                    raise ValueError(f"Invalid score range for {component['name']}.")
                value += score / maximum * number(weight["percentage"])
            results[key] = value
        if period is None:
            results["overall"] = (
                results["midterm"] * number(policy["midterm_weight"])
                + results["final"] * number(policy["final_weight"])
            ) / 100
        output = {k: rounded(v) for k, v in results.items()}
        if include_equivalents:
            for key, field in [
                ("midterm", "midterm_equiv"),
                ("final", "finals_equiv"),
                ("overall", "final_equiv"),
            ]:
                if key in results:
                    output[field] = GradeCalculator.grade_point(results[key])
            if "overall" in results:
                output["remarks"] = "Failed" if output["final_equiv"] == 5 else "Passed"
        return output
