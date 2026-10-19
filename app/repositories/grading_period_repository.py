from app.database.connection import get_connection


class GradingPeriodRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT period_id, name, start_date, end_date, school_year, semester, period_order
                FROM grading_periods ORDER BY period_order, start_date
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
                SELECT period_id, name, start_date, end_date, school_year, semester, period_order
                FROM grading_periods WHERE period_id = %s
            """, (period_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, period_id, name, start_date, end_date, school_year, semester, period_order=1):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO grading_periods
                    (period_id, name, start_date, end_date, school_year, semester, period_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (period_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    school_year = EXCLUDED.school_year,
                    semester = EXCLUDED.semester,
                    period_order = EXCLUDED.period_order
            """, (period_id, name, start_date, end_date, school_year, semester, period_order))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, period_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM grading_periods WHERE period_id = %s",
                (period_id,)
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
