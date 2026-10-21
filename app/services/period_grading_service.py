from psycopg.rows import dict_row
from app.database.connection import get_connection
from app.calculator.period_calculator import PeriodCalculator
from app.repositories import period_grading_repository as repository


class PeriodGradingService:
    def __init__(self, calculator=None, connection_factory=None):
        self.calculator = calculator or PeriodCalculator()
        self.connection_factory = connection_factory or get_connection

    def save_policy(self, policy, weights):
        with self.connection_factory() as c:
            with c.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                cursor.execute(
                    "SELECT * FROM class WHERE class_id=%s FOR UPDATE",
                    (policy["class_id"],),
                )
                offering = cursor.fetchone()
                if not offering:
                    raise ValueError("Class offering not found.")
                ids = [w["component_id"] for w in weights]
                cursor.execute(
                    "SELECT * FROM grade_component WHERE component_id=ANY(%s)", (ids,)
                )
                components = cursor.fetchall()
                self.calculator.validate_policy(policy, weights, components)
                cursor.execute(
                    "SELECT * FROM grading_period WHERE period_id=ANY(%s)",
                    ([policy["midterm_period_id"], policy["final_period_id"]],),
                )
                periods = cursor.fetchall()
                if len(periods) != 2 or any(
                    (p["school_year"], p["semester"])
                    != (offering["school_year"], offering["semester"])
                    for p in periods
                ):
                    raise ValueError(
                        "Periods must match the class school year and semester."
                    )
                repository.save_policy(cursor, policy, weights)

    def calculate_and_save(self, enrollment_id, period=None):
        with self.connection_factory() as c:
            with c.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                cursor.execute(
                    "SELECT class_id FROM enrollment WHERE enrollment_id=%s",
                    (enrollment_id,),
                )
                enrollment = cursor.fetchone()
                if not enrollment:
                    raise ValueError("Enrollment not found.")
                policy, weights, components = repository.context(
                    cursor, enrollment["class_id"]
                )
                cursor.execute(
                    "SELECT * FROM grade_component_score WHERE enrollment_id=%s",
                    (enrollment_id,),
                )
                result = self.calculator.calculate(
                    policy,
                    weights,
                    components,
                    cursor.fetchall(),
                    include_equivalents=True,
                    period=period,
                )
                repository.save_result(cursor, enrollment_id, result)
                return {
                    key: result[key]
                    for key in ("midterm", "final", "overall")
                    if key in result
                }
