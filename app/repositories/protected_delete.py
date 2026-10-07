"""Conservative deletion policy: never cascade away academic evidence."""
from psycopg import sql
from app.database.connection import get_connection


TARGETS = {
    'teachers': ('teacher_id', [('class_offerings', 'teacher_id')]),
    'subjects': ('subject_id', [('class_offerings', 'subject_id')]),
    'grading_periods': ('period_id', [('grade_components', 'period_id')]),
    'class_offerings': ('offering_id', [('enrollments', 'offering_id'), ('grade_percentages', 'offering_id')]),
    'grade_percentages': ('percentage_id', [('grade_components', 'percentage_id')]),
    'grade_components': ('component_id', [('grade_component_scores', 'component_id')]),
}


def delete_unreferenced(table, identifier):
    key, dependents = TARGETS[table]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL('SELECT {} FROM {} WHERE {} = %s FOR UPDATE').format(
                sql.Identifier(key), sql.Identifier(table), sql.Identifier(key)), (identifier,))
            if cursor.fetchone() is None:
                raise ValueError('Record no longer exists.')
            for child, foreign_key in dependents:
                cursor.execute(sql.SQL('SELECT 1 FROM {} WHERE {} = %s LIMIT 1').format(
                    sql.Identifier(child), sql.Identifier(foreign_key)), (identifier,))
                if cursor.fetchone():
                    raise ValueError('This record is referenced by academic records. Deletion is blocked to preserve evidence.')
            cursor.execute(sql.SQL('DELETE FROM {} WHERE {} = %s').format(
                sql.Identifier(table), sql.Identifier(key)), (identifier,))
