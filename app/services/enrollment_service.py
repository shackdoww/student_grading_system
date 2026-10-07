from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.class_offering_repository import ClassOfferingRepository
from uuid import uuid4
from datetime import date
from psycopg.errors import UniqueViolation

class EnrollmentService:
    def __init__(self):
        self.repository = EnrollmentRepository()
        self.student_repository = StudentRepository()
        self.offering_repository = ClassOfferingRepository()

    def get_by_student(self, student_id):
        if not self.student_repository.find_by_id(student_id):
            raise ValueError("Student not found.")
        return self.repository.find_by_student_id(student_id)

    def get_by_offering(self, offering_id):
        if not self.offering_repository.find_by_id(offering_id):
            raise ValueError("Class offering not found.")
        return self.repository.find_by_offering_id(offering_id)

    def get(self, enrollment_id):
        enrollment = self.repository.find_by_id(enrollment_id)
        if not enrollment:
            raise ValueError("Enrollment not found.")
        return enrollment

    def validate_membership(self, student_id, offering_id):
        if not self.student_repository.find_by_id(student_id):
            raise ValueError("Student not found.")
        if not self.offering_repository.find_by_id(offering_id):
            raise ValueError("Class offering not found.")

    def enroll(self, student_id, offering_id, status='Active', enroll_date=None):
        """Create-only enrollment; generated keys never overwrite another record."""
        self.validate_membership(student_id, offering_id)
        if self.repository.find_by_student_and_offering(student_id, offering_id):
            raise ValueError('This student is already enrolled in this class offering.')
        enrollment_id = 'E-' + uuid4().hex
        try:
            self.repository.create(enrollment_id, enroll_date or date.today(), status, student_id, offering_id)
        except UniqueViolation as error:
            if error.diag.constraint_name == 'unique_student_offering':
                raise ValueError('This student is already enrolled in this class offering.') from error
            raise
        return enrollment_id

    def save(self, enrollment_id, enroll_date, status, student_id, offering_id):
        self.validate_membership(student_id, offering_id)

        existing_id = self.repository.find_by_student_and_offering(
            student_id, offering_id
        )
        if existing_id and existing_id != enrollment_id:
            raise ValueError(
                "This student is already enrolled in this class offering."
            )

        self.repository.save(
            enrollment_id, enroll_date, status, student_id, offering_id
        )

    def delete(self, enrollment_id):
        if not self.repository.delete(enrollment_id):
            raise ValueError("Enrollment not found.")
