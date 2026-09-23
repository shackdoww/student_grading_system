from app.database.connection import get_connection


class SubjectRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT subject_id, subject_code, subject_name, description, units
                FROM subjects ORDER BY subject_code
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, subject_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT subject_id, subject_code, subject_name, description, units
                FROM subjects WHERE subject_id = %s
            """, (subject_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, subject_id, subject_code, subject_name, description, units):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO subjects
                    (subject_id, subject_code, subject_name, description, units)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (subject_id) DO UPDATE SET
                    subject_code = EXCLUDED.subject_code,
                    subject_name = EXCLUDED.subject_name,
                    description = EXCLUDED.description,
                    units = EXCLUDED.units
            """, (subject_id, subject_code, subject_name, description, units))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, subject_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
