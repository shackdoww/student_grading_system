"""Conservative deletion policy: never cascade away academic evidence."""
from psycopg import sql
from app.database.connection import get_connection


TARGETS = {
    'teacher': ('teacher_id',[('class','teacher_id'),('user_accounts','teacher_id')]),
    'subject': ('subject_id',[('class','subject_id')]),
    'grading_period': ('period_id',[('grade_component','period_id'),('grading_policy','midterm_period_id'),('grading_policy','final_period_id')]),
    'class': ('class_id',[('enrollment','class_id'),('grade_percentage','class_id'),('grading_policy','class_id')]),
    'grade_percentage': ('percentage_id',[]),
    'grade_component': ('component_id',[('grade_component_score','component_id'),('grade_percentage','component_id')]),
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
                column = sql.Identifier('class_code') if child == 'class' else sql.SQL('1')
                cursor.execute(sql.SQL('SELECT {} FROM {} WHERE {} = %s LIMIT 1').format(
                    column, sql.Identifier(child), sql.Identifier(foreign_key)), (identifier,))
                dependent = cursor.fetchone()
                if dependent:
                    detail = f' Class {dependent[0]} depends on this record.' if child == 'class' else f' Dependent records exist in {child}.'
                    raise ValueError('Deletion is blocked to preserve evidence.' + detail)
            cursor.execute(sql.SQL('DELETE FROM {} WHERE {} = %s').format(
                sql.Identifier(table), sql.Identifier(key)), (identifier,))
