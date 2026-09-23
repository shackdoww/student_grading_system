from app.database.connection import get_connection


class GradeRepository:

    def save(self, grade_id, final_grade, remarks, date_encoded, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO grades (
                    grade_id,
                    final_grade,
                    remarks,
                    date_encoded,
                    enrollment_id
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (enrollment_id)
                DO UPDATE SET
                    final_grade = EXCLUDED.final_grade,
                    remarks = EXCLUDED.remarks,
                    date_encoded = EXCLUDED.date_encoded
                """, (
                    grade_id,
                    final_grade,
                    remarks,
                    date_encoded,
                    enrollment_id
                ))

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def find_by_enrollment_id(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    grade_id,
                    final_grade,
                    remarks,
                    date_encoded,
                    enrollment_id
                FROM grades
                WHERE enrollment_id = %s
            """, (enrollment_id,))

            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
