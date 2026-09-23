from app.database.connection import get_connection


class GradePercentageRepository:

    def find_by_offering_id(self, offering_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT percentage_id, percentage, offering_id
                FROM grade_percentages
                WHERE offering_id = %s
                ORDER BY percentage_id
            """, (offering_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, percentage_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT percentage_id, percentage, offering_id
                FROM grade_percentages
                WHERE percentage_id = %s
            """, (percentage_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, percentage_id, percentage, offering_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO grade_percentages
                    (percentage_id, percentage, offering_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (percentage_id) DO UPDATE SET
                    percentage = EXCLUDED.percentage,
                    offering_id = EXCLUDED.offering_id
            """, (percentage_id, percentage, offering_id))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, percentage_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM grade_percentages WHERE percentage_id = %s",
                (percentage_id,)
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
