from app.database.connection import get_connection


class ClassOfferingRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    co.class_id, co.class_code, co.schedule, co.section,
                    co.school_year, co.semester, co.room, co.teacher_id,
                    t.first_name, t.last_name, co.subject_id,
                    s.subject_code, s.subject_name
                FROM class co
                JOIN teacher t ON co.teacher_id = t.teacher_id
                JOIN subject s ON co.subject_id = s.subject_id
                ORDER BY co.school_year, co.semester, s.subject_code, co.section
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, class_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT class_id, class_code, schedule, section,
                       school_year, semester, room, teacher_id, subject_id
                FROM class WHERE class_id = %s
            """, (class_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, class_id, class_code, schedule, section,
             school_year, semester, room, teacher_id, subject_id, meetings=None):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO class
                    (class_id, class_code, schedule, section, school_year,
                     semester, room, teacher_id, subject_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (class_id) DO UPDATE SET
                    class_code = EXCLUDED.class_code,
                    schedule = EXCLUDED.schedule,
                    section = EXCLUDED.section,
                    school_year = EXCLUDED.school_year,
                    semester = EXCLUDED.semester,
                    room = EXCLUDED.room,
                    teacher_id = EXCLUDED.teacher_id,
                    subject_id = EXCLUDED.subject_id
            """, (class_id, class_code, schedule, section, school_year,
                  semester, room, teacher_id, subject_id))
            if meetings is not None:
                cursor.execute('DELETE FROM class_meeting WHERE class_id=%s',(class_id,))
                for meeting in meetings:
                    cursor.execute('INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES (%s,%s,%s,%s)',
                        (class_id,meeting['weekday'],meeting['start_time'],meeting['end_time']))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, class_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM class WHERE class_id = %s",
                (class_id,)
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
