from psycopg import sql
from psycopg.rows import dict_row
from app.repositories.protected_delete import TARGETS


DELETABLE = dict(TARGETS, **{
    'students': ('student_id', [('enrollments', 'student_id')]),
    'enrollments': ('enrollment_id', [('grade_component_scores', 'enrollment_id'), ('grades', 'enrollment_id'), ('period_grade_results', 'enrollment_id')]),
    'grade_component_scores': ('score_id', []),
    'grades': ('grade_id', []), 'period_grade_results': ('enrollment_id', []),
    'grading_policies': ('offering_id', []),
})
DELETABLE['teachers'] = ('teacher_id', [('class_offerings', 'teacher_id'), ('user_accounts', 'teacher_id')])


class RecordDeletionService:
    def __init__(self, guard):
        self.guard = guard

    def delete(self, table, identifier):
        if table not in DELETABLE:
            raise ValueError('This record type cannot be deleted here.')
        self.guard.require('delete')
        key, dependents = DELETABLE[table]
        with self.guard.auth.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                actor = self.guard.auth.require_admin(self.guard.token, cursor)
                cursor.execute(sql.SQL('SELECT {} FROM {} WHERE {}=%s FOR UPDATE').format(
                    sql.Identifier(key), sql.Identifier(table), sql.Identifier(key)), (identifier,))
                if not cursor.fetchone():
                    raise ValueError('Record no longer exists.')
                for child, foreign_key in dependents:
                    cursor.execute(sql.SQL('SELECT 1 FROM {} WHERE {}=%s LIMIT 1').format(sql.Identifier(child), sql.Identifier(foreign_key)), (identifier,))
                    if cursor.fetchone():
                        raise ValueError('Delete dependent records first. Automatic cascade deletion is not allowed.')
                if table == 'grading_policies':
                    cursor.execute('''SELECT 1 FROM period_grade_results g JOIN enrollments e
                        ON g.enrollment_id=e.enrollment_id WHERE e.offering_id=%s LIMIT 1''', (identifier,))
                    if cursor.fetchone():
                        raise ValueError('Delete persisted period results before removing their grading policy.')
                    cursor.execute('DELETE FROM period_category_weights WHERE offering_id=%s', (identifier,))
                cursor.execute(sql.SQL('DELETE FROM {} WHERE {}=%s').format(sql.Identifier(table), sql.Identifier(key)), (identifier,))
                cursor.execute('INSERT INTO security_events(actor_id,action,target) VALUES (%s,%s,%s)',
                               (actor['user_id'], 'record.deleted', f'{table}:{identifier}'))
