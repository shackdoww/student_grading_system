from app.database.connection import get_connection


class EnrollmentRepository:

    def find_by_id(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    e.enrollment_id,
                    e.enroll_date,
                    e.status,
                    e.student_id,
                    e.offering_id,
                    s.first_name,
                    s.last_name,
                    s.student_id,
                    co.class_code,
                    co.section,
                    sub.subject_code,
                    sub.subject_name
                FROM enrollments e
                JOIN students s
                    ON e.student_id = s.student_id
                JOIN class_offerings co
                    ON e.offering_id = co.offering_id
                JOIN subjects sub
                    ON co.subject_id = sub.subject_id
                WHERE e.enrollment_id = %s
            """, (enrollment_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def find_by_student_id(self, student_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
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
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_student_and_offering(self, student_id, offering_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT enrollment_id
                FROM enrollments
                WHERE student_id = %s
                  AND offering_id = %s
            """, (student_id, offering_id))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()
            connection.close()

    def save(self, enrollment_id, enroll_date, status, student_id, offering_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO enrollments (
                    enrollment_id, enroll_date, status, student_id, offering_id
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (enrollment_id)
                DO UPDATE SET
                    enroll_date = EXCLUDED.enroll_date,
                    status = EXCLUDED.status,
                    student_id = EXCLUDED.student_id,
                    offering_id = EXCLUDED.offering_id
            """, (enrollment_id, enroll_date, status, student_id, offering_id))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "DELETE FROM enrollments WHERE enrollment_id = %s",
                (enrollment_id,)
            )
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
