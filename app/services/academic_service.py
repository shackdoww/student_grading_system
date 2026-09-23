from app.repositories.teacher_repository import TeacherRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.class_offering_repository import ClassOfferingRepository
from app.repositories.grading_period_repository import GradingPeriodRepository
from app.repositories.grade_percentage_repository import GradePercentageRepository
from app.repositories.grade_component_repository import GradeComponentRepository

class AcademicService:
    def __init__(self):
        self.teachers = TeacherRepository()
        self.subjects = SubjectRepository()
        self.offerings = ClassOfferingRepository()
        self.periods = GradingPeriodRepository()
        self.percentages = GradePercentageRepository()
        self.components = GradeComponentRepository()

    def save_teacher(self, *args):
        self.teachers.save(*args)

    def save_subject(self, *args):
        self.subjects.save(*args)

    def save_offering(self, offering_id, class_code, schedule, section,
                      school_year, semester, room, teacher_id, subject_id):
        if not self.teachers.find_by_id(teacher_id):
            raise ValueError("Teacher not found.")
        if not self.subjects.find_by_id(subject_id):
            raise ValueError("Subject not found.")
        self.offerings.save(
            offering_id, class_code, schedule, section, school_year,
            semester, room, teacher_id, subject_id
        )

    def save_period(self, *args):
        self.periods.save(*args)

    def save_percentage(self, percentage_id, percentage, offering_id):
        if not self.offerings.find_by_id(offering_id):
            raise ValueError("Class offering not found.")
        percentage = float(percentage)
        if percentage <= 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100.")
        self.percentages.save(percentage_id, percentage, offering_id)

    def save_component(self, component_id, name, component_type, max_score,
                       description, period_id, percentage_id):
        if not self.periods.find_by_id(period_id):
            raise ValueError("Grading period not found.")
        if not self.percentages.find_by_id(percentage_id):
            raise ValueError("Grade percentage not found.")
        max_score = float(max_score)
        if max_score <= 0:
            raise ValueError("Maximum score must be greater than zero.")
        self.components.save(
            component_id, name, component_type, max_score,
            description, period_id, percentage_id
        )
