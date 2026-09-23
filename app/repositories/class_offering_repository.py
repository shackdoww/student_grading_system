from app.database.connection import get_connection


class ClassOfferingRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    co.offering_id,
                    co.class_code,
                    co.schedule,
                    co.section,
                    co.school_year,
                    co.semester,
                    co.room,
                    co.teacher_id,
                    t.first_name,
                    t.last_name,
                    co.subject_id,
                    s.subject_code,
                    s.subject_name
                FROM class_offerings co
                JOIN teachers t
                    ON co.teacher_id = t.teacher_id
                JOIN subjects s
                    ON co.subject_id = s.subject_id
                ORDER BY co.school_year, co.semester, s.subject_code, co.section
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, offering_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    offering_id, class_code, schedule, section,
                    school_year, semester, room, teacher_id, subject_id
                FROM class_offerings
                WHERE offering_id = %s
            """, (offering_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(
        self,
        offering_id,
        class_code,
        schedule,
        section,
        school_year,
        semester,
        room,
        teacher_id,
        subject_id
    ):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO class_offerings (
                    offering_id, class_code, schedule, section,
                    school_year, semester, room, teacher_id, subject_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (offering_id)
                DO UPDATE SET
                    class_code = EXCLUDED.class_code,
                    schedule = EXCLUDED.schedule,
                    section = EXCLUDED.section,
                    school_year = EXCLUDED.school_year,
                    semester = EXCLUDED.semester,
                    room = EXCLUDED.room,
                    teacher_id = EXCLUDED.teacher_id,
                    subject_id = EXCLUDED.subject_id
            """, (
                offering_id,
                class_code,
                schedule,
                section,
                school_year,
                semester,
                room,
                teacher_id,
                subject_id
            ))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
