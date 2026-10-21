import re

from app.repositories.student_repository import StudentRepository
from psycopg.errors import UniqueViolation


class StudentService:
    def __init__(self):
        self.repository = StudentRepository()

    def get_all(self):
        return self.repository.find_all()

    def get(self, student_id):
        student = self.repository.find_by_id(student_id)
        if not student:
            raise ValueError("Student not found.")
        return student

    @staticmethod
    def validate(student_id, first_name, last_name, email, program, status, year_level):
        if not all(
            str(v or "").strip()
            for v in [student_id, first_name, last_name, program, status]
        ):
            raise ValueError("Student number, names, program and status are required.")
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address or leave it blank.")
        if not str(year_level).isdigit() or not 1 <= int(year_level) <= 6:
            raise ValueError("Year level must be between 1 and 6.")

    def create(
        self, student_id, first_name, last_name, email, program, status, year_level=1
    ):
        self.validate(
            student_id, first_name, last_name, email, program, status, year_level
        )
        if self.repository.find_by_id(student_id):
            raise ValueError(
                "Student number already exists. Use Edit student to change it."
            )
        try:
            self.repository.create(
                student_id,
                first_name,
                last_name,
                email,
                program,
                status,
                int(year_level),
            )
        except UniqueViolation as error:
            raise ValueError("Student number or email already exists.") from error

    def save(
        self, student_id, first_name, last_name, email, program, status, year_level=1
    ):
        self.validate(
            student_id, first_name, last_name, email, program, status, year_level
        )
        self.repository.save(
            student_id, first_name, last_name, email, program, status, int(year_level)
        )
