from app.database.connection import get_connection


class ScoreRepository:

    def find_by_enrollment_id(self, enrollment_id):
        connection = get_connection()
        cursor = connection.cursor()

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
                           gp.offering_id,
                           gcp.name,
                           gcp.start_date,
                           gcp.end_date
                       FROM grade_component_scores gcs
                                JOIN grade_components gc
                                     ON gcs.component_id = gc.component_id
                                JOIN grade_percentages gp
                                     ON gc.percentage_id = gp.percentage_id
                                JOIN grading_periods gcp
                                     ON gc.period_id = gcp.period_id
                       WHERE gcs.enrollment_id = %s
                       ORDER BY gcp.start_date, gc.component_id
                       """, (enrollment_id,))

        scores = cursor.fetchall()

        cursor.close()
        connection.close()

        return scores