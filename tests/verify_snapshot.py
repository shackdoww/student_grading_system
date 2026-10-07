"""Read-only comparison of GUI snapshots against the established repositories."""

from app.gui.data_snapshot import load_snapshot
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.grading_period_repository import GradingPeriodRepository
from app.repositories.class_offering_repository import ClassOfferingRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.score_repository import ScoreRepository
from app.services.grading_service import GradingService


def main():
    snapshot = load_snapshot()
    for cached, repository in ((snapshot.students, StudentRepository()),
                               (snapshot.teachers, TeacherRepository()),
                               (snapshot.subjects, SubjectRepository()),
                               (snapshot.periods, GradingPeriodRepository()),
                               (snapshot.offerings, ClassOfferingRepository())):
        assert cached() == repository.find_all(), repository.__class__.__name__
    enrollments = EnrollmentRepository()
    components = GradeComponentRepository()
    grading = GradingService()
    scores = ScoreRepository()
    for student in snapshot.students()[:3]:
        rows = snapshot.enrollments_for_student(student[0])
        assert rows == enrollments.find_by_student_id(student[0])
        for enrollment in rows:
            eid = enrollment[0]
            assert snapshot.saved_grade(eid) == grading.get_saved_grade(eid)
            assert snapshot._scores.get(eid, []) == scores.find_by_enrollment_id(eid)
            try:
                grade = grading.calculate_grade(eid)
            except ValueError:
                try:
                    snapshot.calculate_grade(eid)
                except ValueError:
                    pass
                else:
                    raise AssertionError('Snapshot accepted a grade rejected by the service')
            else:
                assert grade == snapshot.calculate_grade(eid)
    for offering in snapshot.offerings()[:3]:
        oid = offering[0]
        assert snapshot.enrollments_for_offering(oid) == enrollments.find_by_offering_id(oid)
        assert snapshot.components_for_offering(oid) == components.find_by_offering_id(oid)
    print('Snapshot rows, joins, scores and calculated grades match the existing repositories/services.')


if __name__ == '__main__':
    main()
