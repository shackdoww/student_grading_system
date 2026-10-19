"""Conservative deletion policy: never cascade away academic evidence."""
from psycopg import sql
from app.database.connection import get_connection


TARGETS = {
    'teachers': ('teacher_id', [('class_offerings', 'teacher_id'), ('user_accounts', 'teacher_id')]),
    'subjects': ('subject_id', [('class_offerings', 'subject_id')]),
    'grading_periods': ('period_id', [('grade_components', 'period_id'), ('grading_policies', 'midterm_period_id'), ('grading_policies', 'final_period_id')]),
    'class_offerings': ('offering_id', [('enrollments', 'offering_id'), ('grade_percentages', 'offering_id'), ('grading_policies', 'offering_id')]),
    'grade_percentages': ('percentage_id', [('grade_components', 'percentage_id'), ('period_category_weights', 'percentage_id')]),
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
                column = sql.Identifier('class_code') if child == 'class_offerings' else sql.SQL('1')
                cursor.execute(sql.SQL('SELECT {} FROM {} WHERE {} = %s LIMIT 1').format(
                    column, sql.Identifier(child), sql.Identifier(foreign_key)), (identifier,))
                dependent = cursor.fetchone()
                if dependent:
                    detail = f' Class {dependent[0]} depends on this record.' if child == 'class_offerings' else f' Dependent records exist in {child}.'
                    raise ValueError('Deletion is blocked to preserve evidence.' + detail)
            cursor.execute(sql.SQL('DELETE FROM {} WHERE {} = %s').format(
                sql.Identifier(table), sql.Identifier(key)), (identifier,))
