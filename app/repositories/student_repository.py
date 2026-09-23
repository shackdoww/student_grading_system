from app.database.connection import get_connection


class StudentRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
                       SELECT student_id, first_name, last_name, email, program, status
                       FROM students
                       ORDER BY last_name, first_name
                       """)

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return students

    def find_by_id(self, student_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
                       SELECT student_id, first_name, last_name, email, program, status
                       FROM students
                       WHERE student_id = %s
                       """, (student_id,))

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student