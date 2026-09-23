from app.database.connection import get_connection


class GradingPeriodRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    period_id, name, start_date, end_date,
                    school_year, semester
                FROM grading_periods
                ORDER BY start_date
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, period_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    period_id, name, start_date, end_date,
                    school_year, semester
                FROM grading_periods
                WHERE period_id = %s
            """, (period_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
