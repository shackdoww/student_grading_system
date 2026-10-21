import pytest
from app.calculator.period_calculator import PeriodCalculator


def example():
    policy = dict(class_id='O', midterm_period_id='M', final_period_id='F', midterm_weight=40, final_weight=60)
    weights = [dict(component_id=p+c, percentage=w)
               for p in ['M', 'F'] for c, w in [('Q', 20), ('L', 30), ('E', 50)]]
    components = [dict(component_id=p+c, name=p+c, period_id=p, percentage_id=c, max_score=50)
                  for p in ['M', 'F'] for c in ['Q', 'L', 'E']]
    scores = [dict(component_id=c['component_id'], score=40 if c['period_id'] == 'M' else 45) for c in components]
    return policy, weights, components, scores


def test_period_and_overall_normalization():
    assert PeriodCalculator().calculate(*example()) == dict(midterm=80, final=90, overall=86)


def test_recalculation_with_changed_configuration():
    policy, weights, components, scores = example()
    policy.update(midterm_weight=60, final_weight=40)
    assert PeriodCalculator().calculate(policy, weights, components, scores)['overall'] == 84
    assert [s['score'] for s in scores] == [40]*3 + [45]*3


@pytest.mark.parametrize('case', ['missing', 'range', 'total', 'duplicate', 'nonfinite', 'same_period'])
def test_invalid_configuration_and_evidence(case):
    policy, weights, components, scores = example()
    if case == 'missing': scores.pop()
    if case == 'range': scores[0]['score'] = 51
    if case == 'total': weights[0]['percentage'] = 21
    if case == 'duplicate': weights.append(dict(weights[0]))
    if case == 'nonfinite': scores[0]['score'] = float('nan')
    if case == 'same_period': policy['final_period_id'] = 'M'
    with pytest.raises(ValueError):
        PeriodCalculator().calculate(policy, weights, components, scores)
