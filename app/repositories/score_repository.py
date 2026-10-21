from app.database.connection import get_connection


class ScoreRepository:

    def find_by_enrollment_id(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    gcs.score_id,
                    gcs.score,
                    gcs.remarks,
                    gcs.date_recorded,
                    gc.component_id,
                    gc.name,
                    gc.type,
                    gc.max_score,
                    gc.description,
                    gp.percentage_id,
                    gp.percentage,
                    gp.class_id,
                    gcp.name,
                    gcp.start_date,
                    gcp.end_date
                FROM grade_component_score gcs
                JOIN grade_component gc
                    ON gcs.component_id = gc.component_id
                JOIN grade_percentage gp
                    ON gc.component_id = gp.component_id
                JOIN enrollment e ON e.enrollment_id=gcs.enrollment_id AND e.class_id=gp.class_id
                JOIN grading_period gcp
                    ON gc.period_id = gcp.period_id
                WHERE gcs.enrollment_id = %s
                ORDER BY gcp.start_date, gc.component_id
            """, (enrollment_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def save(self, score_id, score, remarks, date_recorded, enrollment_id, component_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO grade_component_score (
                    score_id,
                    score,
                    remarks,
                    date_recorded,
                    enrollment_id,
                    component_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (enrollment_id, component_id)
                DO UPDATE SET
                    score = EXCLUDED.score,
                    remarks = EXCLUDED.remarks,
                    date_recorded = EXCLUDED.date_recorded
            """, (
                score_id,
                score,
                remarks or None,
                date_recorded,
                enrollment_id,
                component_id
            ))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete(self, score_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "DELETE FROM grade_component_score WHERE score_id = %s",
                (score_id,)
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
