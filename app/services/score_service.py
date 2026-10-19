from datetime import date
from math import isfinite

from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.score_repository import ScoreRepository


class ScoreService:

    def __init__(self):
        self.score_repository = ScoreRepository()
        self.component_repository = GradeComponentRepository()
        self.enrollment_repository = EnrollmentRepository()

    def record_score(
        self,
        score_id,
        enrollment_id,
        component_id,
        score,
        remarks=""
    ):
        enrollment = self.enrollment_repository.find_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found.")

        component = self.component_repository.find_by_id(component_id)
        if not component:
            raise ValueError("Grade component not found.")

        enrollment_offering_id = enrollment[4]
        component_offering_id = component[8]

        if enrollment_offering_id != component_offering_id:
            raise ValueError(
                "Grade component does not belong to the student's class offering."
            )

        maximum = float(component[3])
        score = float(score)

        if not isfinite(score) or not isfinite(maximum):
            raise ValueError('Score and maximum must be finite numbers.')

        if score < 0 or score > maximum:
            raise ValueError(
                f"Score must be between 0 and {maximum:.2f}."
            )

        self.score_repository.save(
            score_id=score_id,
            score=score,
            remarks=remarks,
            date_recorded=date.today(),
            enrollment_id=enrollment_id,
            component_id=component_id
        )

    def get_scores(self, enrollment_id):
        return self.score_repository.find_by_enrollment_id(enrollment_id)

    def delete_score(self, score_id):
        return self.score_repository.delete(score_id)
