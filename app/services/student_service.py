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

    def delete(self, student_id):
        if not self.repository.delete(student_id):
            raise ValueError("Student not found.")
