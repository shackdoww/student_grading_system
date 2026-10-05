import re

from app.repositories.student_repository import StudentRepository

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

    def save(self, student_id, first_name, last_name, email, program, status):
        if not all([student_id, first_name, last_name, email, program, status]):
            raise ValueError("All student fields are required.")
        self.repository.save(student_id, first_name, last_name, email, program, status)

    def validate_import(self, students):
        required = ("student_id", "first_name", "last_name", "email", "program", "status")
        errors = []
        seen_ids = set()
        seen_emails = set()

        for number, student in enumerate(students, start=2):
            missing = [field for field in required if not str(student.get(field, "")).strip()]
            if missing:
                errors.append(f"Row {number}: missing {', '.join(missing)}.")
                continue

            student["student_id"] = str(student["student_id"]).strip()
            student["first_name"] = str(student["first_name"]).strip()
            student["last_name"] = str(student["last_name"]).strip()
            student["email"] = str(student["email"]).strip().lower()
            student["program"] = str(student["program"]).strip()
            student["status"] = str(student["status"]).strip()

            if student["student_id"] in seen_ids:
                errors.append(f"Row {number}: duplicate Student ID '{student['student_id']}' in CSV.")
            seen_ids.add(student["student_id"])

            if student["email"] in seen_emails:
                errors.append(f"Row {number}: duplicate email '{student['email']}' in CSV.")
            seen_emails.add(student["email"])

            if not re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", student["email"]):
                errors.append(f"Row {number}: invalid email '{student['email']}'.")

        if errors:
            return errors

        existing = self.repository.get_import_conflicts(
            list(seen_ids), list(seen_emails)
        )
        existing_by_id = {row[0]: row[1] for row in existing}
        for number, student in enumerate(students, start=2):
            if student["email"] in set(existing_by_id.values()):
                owner = next((sid for sid, email in existing_by_id.items() if email == student["email"]), None)
                if owner != student["student_id"]:
                    errors.append(
                        f"Row {number}: email '{student['email']}' already belongs to Student ID '{owner}'."
                    )

        return errors

    def import_students(self, students):
        errors = self.validate_import(students)
        if errors:
            raise ValueError("\n".join(errors))
        self.repository.save_many(students)

    def delete(self, student_id):
        if not self.repository.delete(student_id):
            raise ValueError("Student not found.")
