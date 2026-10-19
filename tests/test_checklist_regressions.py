from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.calculator.grade_calculator import GradeCalculator
from app.calculator.period_calculator import PeriodCalculator
from app.services.student_service import StudentService


@pytest.mark.parametrize('percentage,expected', [
    ('100', 1), ('97', 1), ('96.999', 1.25), ('94', 1.25),
    ('93.999', 1.5), ('91', 1.5), ('88', 1.75), ('85', 2),
    ('82', 2.25), ('79', 2.5), ('76', 2.75), ('75', 3), ('74.999', 5), ('0', 5),
])
def test_grade_points_use_unrounded_percentage(percentage, expected):
    assert GradeCalculator.grade_point(Decimal(percentage)) == expected


def rubric_example(scores):
    policy = dict(offering_id='O', midterm_period_id='M', final_period_id='F', midterm_weight=40, final_weight=60)
    weights = [dict(period_id=p, percentage_id=c, weight=w)
               for p in ['M', 'F'] for c, w in [('Q', 20), ('L', 30), ('E', 50)]]
    components = [dict(component_id=p+c, name=p+c, period_id=p, percentage_id=c, max_score=maximum)
                  for p in ['M', 'F'] for c, maximum in [('Q', 50), ('L', 100), ('E', 100)]]
    evidence = [dict(component_id=c['component_id'], score=s) for c, s in zip(components, scores)]
    return policy, weights, components, evidence


@pytest.mark.parametrize('scores,percentages,points,recalculated', [
    ([40,90,75,45,85,80], [80.5,83.5,82.3], [2.5,2.25,2.25], [81,82.5]),
    ([20,60,55,30,70,65], [53.5,65.5,60.7], [5,5,5], [52,60.1]),
    ([50,100,100,48,95,92], [100,93.7,96.22], [1,1.5,1.25], [100,96.22]),
])
def test_checklist_grades_and_recalculation(scores, percentages, points, recalculated):
    args = rubric_example(scores)
    result = PeriodCalculator().calculate(*args, include_equivalents=True)
    assert [result[k] for k in ['midterm','final','overall']] == percentages
    assert [result[k] for k in ['midterm_equiv','finals_equiv','final_equiv']] == points
    assert result['remarks'] == ('Failed' if points[2] == 5 else 'Passed')
    for weight, value in zip(args[1][:3], [30,30,40]):
        weight['weight'] = value
    updated = PeriodCalculator().calculate(*args, include_equivalents=True)
    assert [updated[k] for k in ['midterm','overall']] == recalculated
    assert [r['score'] for r in args[3]] == scores


def test_conversion_happens_before_rounding_period_grade():
    policy, weights, components, scores = rubric_example([40,90,75,45,85,80])
    for c in components:
        c['max_score'] = 100
    for s in scores:
        s['score'] = Decimal('74.999')
    result = PeriodCalculator().calculate(policy, weights, components, scores, include_equivalents=True)
    assert result['overall'] == 75
    assert result['final_equiv'] == 5
    assert result['remarks'] == 'Failed'


def test_adding_existing_student_cannot_overwrite_details():
    service = StudentService()
    service.repository = MagicMock()
    service.repository.find_by_id.return_value = ('S','Juan','Dela Cruz',None,'BSCS','Active',2)
    with pytest.raises(ValueError, match='already exists'):
        service.create('S','Other','Person','','BSIT','Active',2)
    service.repository.save.assert_not_called()
    service.repository.create.assert_not_called()


def test_student_import_accepts_normal_email():
    service = StudentService()
    service.repository = MagicMock()
    service.repository.get_import_conflicts.return_value = []
    rows = [dict(student_id='S',first_name='Juan',last_name='Dela Cruz',email='juan@example.edu',program='BSCS',status='Active')]
    assert service.validate_import(rows) == []


@pytest.mark.parametrize('bad', ['nan','inf','-inf'])
def test_legacy_calculator_rejects_nonfinite_scores(bad):
    row = ('SC',bad,'',None,'C','Quiz','Quiz',50,'','P',100,'O','Midterm',None,None)
    with pytest.raises(ValueError, match='finite'):
        GradeCalculator().calculate([row])


def test_blank_period_weight_has_a_clear_validation_error():
    policy, weights, components, scores = rubric_example([40,90,75,45,85,80])
    weights[0]['weight']=''
    with pytest.raises(ValueError,match='number'):
        PeriodCalculator().calculate(policy,weights,components,scores)
