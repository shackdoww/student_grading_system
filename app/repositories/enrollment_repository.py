from app.database.connection import get_connection


class EnrollmentRepository:

    def find_by_student_id(self, student_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
                       SELECT
                           e.enrollment_id,
                           e.enroll_date,
                           e.status,
                           co.offering_id,
                           co.class_code,
                           co.schedule,
                           co.section,
                           co.school_year,
                           co.semester,
                           co.room,
                           s.subject_id,
                           s.subject_code,
                           s.subject_name,
                           t.teacher_id,
                           t.first_name,
                           t.last_name
                       FROM enrollments e
                                JOIN class_offerings co
                                     ON e.offering_id = co.offering_id
                                JOIN subjects s
                                     ON co.subject_id = s.subject_id
                                JOIN teachers t
                                     ON co.teacher_id = t.teacher_id
                       WHERE e.student_id = %s
                       ORDER BY s.subject_code
                       """, (student_id,))

        enrollments = cursor.fetchall()

        cursor.close()
        connection.close()

        return enrollments