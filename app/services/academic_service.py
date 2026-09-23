from app.repositories.class_offering_repository import ClassOfferingRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.grade_percentage_repository import GradePercentageRepository
from app.repositories.grading_period_repository import GradingPeriodRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository


class AcademicService:
    def __init__(self):
        self.teachers = TeacherRepository()
        self.subjects = SubjectRepository()
        self.offerings = ClassOfferingRepository()
        self.periods = GradingPeriodRepository()
        self.percentages = GradePercentageRepository()
        self.components = GradeComponentRepository()

    def get_teachers(self):
        return self.teachers.find_all()

    def get_subjects(self):
        return self.subjects.find_all()

    def get_offerings(self):
        return self.offerings.find_all()

    def get_periods(self):
        return self.periods.find_all()

    def get_percentages(self, offering_id):
        return self.percentages.find_by_offering_id(offering_id)

    def get_components(self, offering_id):
        return self.components.find_by_offering_id(offering_id)

    def get_teacher(self, teacher_id):
        teacher = self.teachers.find_by_id(teacher_id)
        if not teacher:
            raise ValueError("Teacher not found.")
        return teacher

    def get_subject(self, subject_id):
        subject = self.subjects.find_by_id(subject_id)
        if not subject:
            raise ValueError("Subject not found.")
        return subject

    def save_teacher(self, *args):
        if not all(str(value).strip() for value in args):
            raise ValueError("All teacher fields are required.")
        self.teachers.save(*args)

    def save_subject(self, subject_id, subject_code, subject_name, description, units):
        if not all([subject_id, subject_code, subject_name, str(units).strip()]):
            raise ValueError("Subject ID, code, name, and units are required.")
        units = int(units)
        if units <= 0:
            raise ValueError("Units must be greater than zero.")
        self.subjects.save(
            subject_id, subject_code, subject_name, description, units
        )

    def save_offering(self, offering_id, class_code, schedule, section,
                      school_year, semester, room, teacher_id, subject_id):
        if not all([offering_id, class_code, schedule, section,
                    school_year, semester, teacher_id, subject_id]):
            raise ValueError("Required class offering fields are missing.")
        if not self.teachers.find_by_id(teacher_id):
            raise ValueError("Teacher not found.")
        if not self.subjects.find_by_id(subject_id):
            raise ValueError("Subject not found.")
        self.offerings.save(
            offering_id, class_code, schedule, section, school_year,
            semester, room, teacher_id, subject_id
        )

    def save_period(self, period_id, name, start_date, end_date,
                    school_year, semester):
        if not all([period_id, name, start_date, end_date, school_year, semester]):
            raise ValueError("All grading period fields are required.")
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        self.periods.save(
            period_id, name, start_date, end_date, school_year, semester
        )

    def save_percentage(self, percentage_id, percentage, offering_id):
        if not self.offerings.find_by_id(offering_id):
            raise ValueError("Class offering not found.")
        percentage = float(percentage)
        if percentage <= 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100.")
        self.percentages.save(percentage_id, percentage, offering_id)

    def save_component(self, component_id, name, component_type, max_score,
                       description, period_id, percentage_id):
        if not all([component_id, name, component_type, period_id, percentage_id]):
            raise ValueError("Required grade component fields are missing.")
        if not self.periods.find_by_id(period_id):
            raise ValueError("Grading period not found.")
        percentage = self.percentages.find_by_id(percentage_id)
        if not percentage:
            raise ValueError("Grade percentage not found.")
        max_score = float(max_score)
        if max_score <= 0:
            raise ValueError("Maximum score must be greater than zero.")
        self.components.save(
            component_id, name, component_type, max_score,
            description, period_id, percentage_id
        )

    def delete_teacher(self, teacher_id):
        if not self.teachers.delete(teacher_id):
            raise ValueError("Teacher not found.")

    def delete_subject(self, subject_id):
        if not self.subjects.delete(subject_id):
            raise ValueError("Subject not found.")

    def delete_offering(self, offering_id):
        if not self.offerings.delete(offering_id):
            raise ValueError("Class offering not found.")

    def delete_period(self, period_id):
        if not self.periods.delete(period_id):
            raise ValueError("Grading period not found.")

    def delete_percentage(self, percentage_id):
        if not self.percentages.delete(percentage_id):
            raise ValueError("Grade percentage not found.")

    def delete_component(self, component_id):
        if not self.components.delete(component_id):
            raise ValueError("Grade component not found.")
