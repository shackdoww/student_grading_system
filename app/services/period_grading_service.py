from psycopg.rows import dict_row
from app.database.connection import get_connection
from app.calculator.period_calculator import PeriodCalculator
from app.repositories import period_grading_repository as repository


class PeriodGradingService:
    def __init__(self, calculator=None, connection_factory=None):
        self.calculator = calculator or PeriodCalculator()
        self.connection_factory = connection_factory or get_connection

    def save_policy(self, policy, weights):
        with self.connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                _, _, components = repository.context(cursor, policy['offering_id'])
                self.calculator.validate_policy(policy, weights, components)
                cursor.execute('SELECT * FROM grading_periods WHERE period_id IN (%s,%s)',
                               (policy['midterm_period_id'], policy['final_period_id']))
                periods = cursor.fetchall()
                cursor.execute('SELECT * FROM class_offerings WHERE offering_id=%s', (policy['offering_id'],))
                offering = cursor.fetchone()
                if not offering or len(periods) != 2 or any(
                    p['school_year'] != offering['school_year'] or p['semester'] != offering['semester'] for p in periods):
                    raise ValueError('Periods must match the class school year and semester.')
                repository.save_policy(cursor, policy, weights)

    def calculate_and_save(self, enrollment_id):
        with self.connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                cursor.execute('SELECT offering_id FROM enrollments WHERE enrollment_id=%s', (enrollment_id,))
                enrollment = cursor.fetchone()
                if not enrollment:
                    raise ValueError('Enrollment not found.')
                policy, weights, components = repository.context(cursor, enrollment['offering_id'])
                cursor.execute('SELECT * FROM grade_component_scores WHERE enrollment_id=%s', (enrollment_id,))
                result = self.calculator.calculate(policy, weights, components, cursor.fetchall())
                repository.save_result(cursor, enrollment_id, result)
                return result
