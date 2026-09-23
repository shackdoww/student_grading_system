from app.repositories.score_repository import ScoreRepository
from app.calculator.grade_calculator import GradeCalculator


score_repository = ScoreRepository()
grade_calculator = GradeCalculator()

scores = score_repository.find_by_enrollment_id("E001")

final_grade = grade_calculator.calculate(scores)

print("Final Grade:", final_grade)