"""Separate strategy for rubric period grading; legacy calculation is unchanged."""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from app.calculator.grade_calculator import GradeCalculator


def number(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation,TypeError,ValueError) as error:
        raise ValueError('Enter a number for every score and weight; blank values are not allowed.') from error
    if not result.is_finite():
        raise ValueError('Grades and weights must be finite numbers.')
    return result


def rounded(value):
    return float(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


class PeriodCalculator:
    def validate_policy(self, policy, weights, components):
        if not policy:
            raise ValueError('Configure period grading for this class first.')
        periods = [policy['midterm_period_id'], policy['final_period_id']]
        if periods[0] == periods[1]:
            raise ValueError('Midterm and Final must use distinct periods.')
        overall_weights = [number(policy['midterm_weight']), number(policy['final_weight'])]
        if any(w <= 0 for w in overall_weights) or sum(overall_weights) != 100:
            raise ValueError('Overall period weights must be positive and total 100%.')
        for period in periods:
            category_ids = {c['percentage_id'] for c in components if c['period_id'] == period}
            configured = [w for w in weights if w['period_id'] == period]
            if not category_ids or {w['percentage_id'] for w in configured} != category_ids:
                raise ValueError('Each period needs components and exactly one weight per category.')
            if len(configured) != len(category_ids):
                raise ValueError('Duplicate category weights are not allowed.')
            if any(number(w['weight']) <= 0 for w in configured) or sum(number(w['weight']) for w in configured) != 100:
                raise ValueError('Category weights must be positive and total 100% in each period.')
        if any(w['period_id'] not in periods for w in weights):
            raise ValueError('Weights must belong to the selected periods.')

    def calculate(self, policy, weights, components, scores, include_equivalents=False):
        self.validate_policy(policy, weights, components)
        actual = {s['component_id']: s for s in scores}
        results = {}
        for name, period in [('midterm', policy['midterm_period_id']), ('final', policy['final_period_id'])]:
            grade = Decimal(0)
            for weight in (w for w in weights if w['period_id'] == period):
                category = [c for c in components if c['period_id'] == period and c['percentage_id'] == weight['percentage_id']]
                normalized = []
                for component in category:
                    if component['component_id'] not in actual:
                        raise ValueError(f"Missing score: {component['name']}. Enter zero explicitly for a zero score.")
                    maximum = number(component['max_score'])
                    score = number(actual[component['component_id']]['score'])
                    if maximum <= 0 or score < 0 or score > maximum:
                        raise ValueError(f"Invalid score range for {component['name']}.")
                    normalized.append(score / maximum * 100)
                grade += sum(normalized) / len(normalized) * number(weight['weight']) / 100
            results[name] = grade
        # Use full precision until presentation/persistence, not rounded intermediates.
        results['overall'] = (results['midterm'] * number(policy['midterm_weight']) +
                              results['final'] * number(policy['final_weight'])) / 100
        output = {name: rounded(value) for name, value in results.items()}
        if include_equivalents:
            for key, field in [('midterm', 'midterm_equiv'), ('final', 'finals_equiv'), ('overall', 'final_equiv')]:
                output[field] = GradeCalculator.grade_point(results[key])
            output['remarks'] = 'Failed' if output['final_equiv'] == 5 else 'Passed'
        return output
