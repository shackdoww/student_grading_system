from app.database.connection import get_connection


class GradeComponentRepository:
    def find_by_id(self, component_id):
        with get_connection() as c:
            return c.execute(
                "SELECT component_id,name,type,max_score,description,period_id FROM grade_component WHERE component_id=%s",
                (component_id,),
            ).fetchone()

    def find_by_class_id(self, class_id):
        with get_connection() as c:
            return c.execute(
                """SELECT gc.component_id,gc.name,gc.type,gc.max_score,gc.description,
                gc.period_id,p.name,w.percentage_id,w.percentage FROM grade_component gc
                JOIN grading_period p USING(period_id) JOIN grade_percentage w USING(component_id)
                WHERE w.class_id=%s ORDER BY p.period_order,gc.component_id""",
                (class_id,),
            ).fetchall()

    def save(
        self, component_id, name, component_type, max_score, description, period_id
    ):
        with get_connection() as c:
            c.execute(
                """INSERT INTO grade_component(component_id,name,type,max_score,description,period_id)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(component_id) DO UPDATE SET
                name=EXCLUDED.name,type=EXCLUDED.type,max_score=EXCLUDED.max_score,
                description=EXCLUDED.description,period_id=EXCLUDED.period_id""",
                (
                    component_id,
                    name,
                    component_type,
                    max_score,
                    description or None,
                    period_id,
                ),
            )

    def assigned(self, class_id, component_id):
        with get_connection() as c:
            return (
                c.execute(
                    "SELECT 1 FROM grade_percentage WHERE class_id=%s AND component_id=%s",
                    (class_id, component_id),
                ).fetchone()
                is not None
            )
