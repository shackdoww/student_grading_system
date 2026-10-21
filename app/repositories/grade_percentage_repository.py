from app.database.connection import get_connection


class GradePercentageRepository:
    def find_by_class_id(self, class_id):
        with get_connection() as c:
            return c.execute(
                "SELECT percentage_id,percentage,class_id,component_id FROM grade_percentage WHERE class_id=%s ORDER BY percentage_id",
                (class_id,),
            ).fetchall()

    def find_by_id(self, percentage_id):
        with get_connection() as c:
            return c.execute(
                "SELECT percentage_id,percentage,class_id,component_id FROM grade_percentage WHERE percentage_id=%s",
                (percentage_id,),
            ).fetchone()
