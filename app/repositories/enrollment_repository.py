from app.database.connection import get_connection


class EnrollmentRepository:
    def update_status(self, enrollment_id, status):
        with get_connection() as connection:
            result = connection.execute('UPDATE enrollment SET status=%s WHERE enrollment_id=%s', (status,enrollment_id))
            if not result.rowcount:
                raise ValueError('Enrollment not found.')

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
                    e.class_id,
                    s.first_name,
                    s.last_name,
                    s.student_id,
                    co.class_code,
                    co.section,
                    sub.subject_code,
                    sub.subject_name
                FROM enrollment e
                JOIN student s
                    ON e.student_id = s.student_id
                JOIN class co
                    ON e.class_id = co.class_id
                JOIN subject sub
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
                    co.class_id,
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
                FROM enrollment e
                JOIN class co
                    ON e.class_id = co.class_id
                JOIN subject s
                    ON co.subject_id = s.subject_id
                JOIN teacher t
                    ON co.teacher_id = t.teacher_id
                WHERE e.student_id = %s
                ORDER BY s.subject_code
            """, (student_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_class_id(self, class_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    e.enrollment_id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.program,
                    e.status
                FROM enrollment e
                JOIN student s
                    ON e.student_id = s.student_id
                WHERE e.class_id = %s
                ORDER BY s.last_name, s.first_name
            """, (class_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_student_and_offering(self, student_id, class_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT enrollment_id
                FROM enrollment
                WHERE student_id = %s
                  AND class_id = %s
            """, (student_id, class_id))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()
            connection.close()

    def save(self, enrollment_id, enroll_date, status, student_id, class_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO enrollment (
                    enrollment_id, enroll_date, status, student_id, class_id
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (enrollment_id)
                DO UPDATE SET
                    enroll_date = EXCLUDED.enroll_date,
                    status = EXCLUDED.status,
                    student_id = EXCLUDED.student_id,
                    class_id = EXCLUDED.class_id
            """, (enrollment_id, enroll_date, status, student_id, class_id))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def create(self, enrollment_id, enroll_date, status, student_id, class_id):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('''INSERT INTO enrollment
                    (enrollment_id,enroll_date,status,student_id,class_id)
                    VALUES (%s,%s,%s,%s,%s)''',
                    (enrollment_id, enroll_date, status, student_id, class_id))

    def delete(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "DELETE FROM enrollment WHERE enrollment_id = %s",
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
