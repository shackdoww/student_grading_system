from app.repositories.class_offering_repository import ClassOfferingRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.grade_percentage_repository import GradePercentageRepository
from app.repositories.grading_period_repository import GradingPeriodRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository


class AcademicService:
    def delete_unreferenced(self, table, identifier):
        from app.repositories.protected_delete import delete_unreferenced
        delete_unreferenced(table, identifier)

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

    def get_percentages(self, class_id):
        return self.percentages.find_by_class_id(class_id)

    def get_components(self, class_id):
        return self.components.find_by_class_id(class_id)

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
        if not all(str(value or '').strip() for i,value in enumerate(args) if i != 3):
            raise ValueError('Teacher ID, names, department and status are required.')
        self.teachers.save(*args)

    def create_teacher(self, teacher_id, first_name, last_name, email, department, status):
        from psycopg.errors import UniqueViolation
        if not all(str(v or '').strip() for v in (teacher_id,first_name,last_name,department,status)):
            raise ValueError('Teacher ID, names, department and status are required.')
        try:
            self.teachers.create(teacher_id,first_name,last_name,email,department,status)
        except UniqueViolation as error:
            raise ValueError('Teacher ID or email already exists.') from error

    def save_subject(self, subject_id, subject_code, subject_name, description, units):
        if not all([subject_id, subject_code, subject_name, str(units).strip()]):
            raise ValueError("Subject ID, code, name, and units are required.")
        units = int(units)
        if units <= 0:
            raise ValueError("Units must be greater than zero.")
        self.subjects.save(
            subject_id, subject_code, subject_name, description, units
        )

    def save_offering(self, class_id, class_code, schedule, section,
                      school_year, semester, room, teacher_id, subject_id):
        if not all([class_id, class_code, schedule, section,
                    school_year, semester, teacher_id, subject_id]):
            raise ValueError("Required class offering fields are missing.")
        if not self.teachers.find_by_id(teacher_id):
            raise ValueError("Teacher not found.")
        if not self.subjects.find_by_id(subject_id):
            raise ValueError("Subject not found.")
        from app.services.scheduling import normalize_meetings,format_schedule
        meetings=normalize_meetings(schedule)
        schedule=format_schedule(meetings)
        self.offerings.save(
            class_id, class_code, schedule, section, school_year,
            semester, room, teacher_id, subject_id, meetings=meetings
        )

    def save_period(self, period_id, name, start_date, end_date,
                    school_year, semester, period_order=1):
        if not all([period_id, name, start_date, end_date, school_year, semester]):
            raise ValueError("All grading period fields are required.")
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        if not str(period_order).isdigit() or int(period_order) < 1:
            raise ValueError('Period order must be a positive integer.')
        self.periods.save(
            period_id, name, start_date, end_date, school_year, semester, int(period_order)
        )

    def save_component(self, component_id, name, component_type, max_score, description, period_id):
        from app.calculator.period_calculator import number
        if not all(str(v or '').strip() for v in (component_id,name,component_type,period_id)):
            raise ValueError('Required grade component fields are missing.')
        if not self.periods.find_by_id(period_id):
            raise ValueError('Grading period not found.')
        maximum=number(max_score)
        if maximum<=0:
            raise ValueError('Maximum score must be greater than zero.')
        self.components.save(component_id,name,component_type,maximum,description,period_id)
