from app.database.connection import get_connection


class GradeComponentRepository:

    def find_by_id(self, component_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    gc.component_id,
                    gc.name,
                    gc.type,
                    gc.max_score,
                    gc.description,
                    gc.period_id,
                    gc.percentage_id,
                    gperc.percentage,
                    gperc.offering_id
                FROM grade_components gc
                JOIN grade_percentages gperc
                    ON gc.percentage_id = gperc.percentage_id
                WHERE gc.component_id = %s
            """, (component_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def find_by_offering_id(self, offering_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    gc.component_id, gc.name, gc.type, gc.max_score,
                    gc.description, gc.period_id, gp.name,
                    gc.percentage_id, gperc.percentage
                FROM grade_components gc
                JOIN grading_periods gp ON gc.period_id = gp.period_id
                JOIN grade_percentages gperc ON gc.percentage_id = gperc.percentage_id
                WHERE gperc.offering_id = %s
                ORDER BY gp.start_date, gc.component_id
            """, (offering_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def save(self, component_id, name, component_type, max_score,
             description, period_id, percentage_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO grade_components
                    (component_id, name, type, max_score, description,
                     period_id, percentage_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (component_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    type = EXCLUDED.type,
                    max_score = EXCLUDED.max_score,
                    description = EXCLUDED.description,
                    period_id = EXCLUDED.period_id,
                    percentage_id = EXCLUDED.percentage_id
            """, (component_id, name, component_type, max_score,
                  description, period_id, percentage_id))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, component_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM grade_components WHERE component_id = %s",
                (component_id,)
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
