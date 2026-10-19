from app.database.connection import get_connection


class TeacherRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT teacher_id, first_name, last_name, email, department, status
                FROM teachers ORDER BY last_name, first_name
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, teacher_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT teacher_id, first_name, last_name, email, department, status
                FROM teachers WHERE teacher_id = %s
            """, (teacher_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, teacher_id, first_name, last_name, email, department, status):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO teachers
                    (teacher_id, first_name, last_name, email, department, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (teacher_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    department = EXCLUDED.department,
                    status = EXCLUDED.status
            """, (teacher_id, first_name, last_name, email or None, department, status))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, teacher_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
