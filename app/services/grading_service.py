from datetime import date

from app.calculator.grade_calculator import GradeCalculator
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.grade_repository import GradeRepository
from app.repositories.score_repository import ScoreRepository


class GradingService:

    def __init__(self):
        self.score_repository = ScoreRepository()
        self.grade_repository = GradeRepository()
        self.enrollment_repository = EnrollmentRepository()
        self.grade_calculator = GradeCalculator()

    def calculate_grade(self, enrollment_id):
        enrollment = self.enrollment_repository.find_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found.")

        scores = self.score_repository.find_by_enrollment_id(enrollment_id)
        if not scores:
            raise ValueError("No grade component scores found for this enrollment.")

        return self.grade_calculator.calculate(scores)

    def get_grade_breakdown(self, enrollment_id):
        enrollment = self.enrollment_repository.find_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found.")

        scores = self.score_repository.find_by_enrollment_id(enrollment_id)
        if not scores:
            raise ValueError("No grade component scores found for this enrollment.")

        return self.grade_calculator.calculate_breakdown(scores)

    def calculate_and_save_grade(self, enrollment_id, grade_id=None):
        final_grade = self.calculate_grade(enrollment_id)

        if grade_id is None:
            grade_id = f"G-{enrollment_id}"

        self.grade_repository.save(
            grade_id=grade_id,
            final_grade=final_grade,
            remarks="Calculated grade",
            date_encoded=date.today(),
            enrollment_id=enrollment_id
        )

        return final_grade

    def get_saved_grade(self, enrollment_id):
        return self.grade_repository.find_by_enrollment_id(enrollment_id)
