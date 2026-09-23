from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.class_offering_repository import ClassOfferingRepository

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

    def save(self, enrollment_id, enroll_date, status, student_id, offering_id):
        if not self.student_repository.find_by_id(student_id):
            raise ValueError("Student not found.")
        if not self.offering_repository.find_by_id(offering_id):
            raise ValueError("Class offering not found.")

        existing_id = self.repository.find_by_student_and_offering(
            student_id, offering_id
        )
        if existing_id and existing_id != enrollment_id:
            raise ValueError(
                f"This student is already enrolled in this class offering "
                f"(Enrollment ID: {existing_id})."
            )

        self.repository.save(
            enrollment_id, enroll_date, status, student_id, offering_id
        )

    def delete(self, enrollment_id):
        if not self.repository.delete(enrollment_id):
            raise ValueError("Enrollment not found.")
