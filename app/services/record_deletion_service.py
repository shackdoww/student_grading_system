from psycopg import sql
from psycopg.rows import dict_row
from app.repositories.protected_delete import TARGETS


DELETABLE = dict(TARGETS, **{
    'student': ('student_id',[('enrollment','student_id')]),
    'enrollment': ('enrollment_id',[('grade_component_score','enrollment_id'),('grade','enrollment_id')]),
    'grade_component_score': ('score_id',[]), 'grade': ('grade_id',[]),
    'grading_policy': ('class_id',[]),
})

class RecordDeletionService:
    def __init__(self, guard):
        self.guard = guard

    def delete(self, table, identifier, source_reference=None):
        return self.delete_many(table, [identifier],source_reference=source_reference)

    def delete_many(self, table, identifiers, source_reference=None):
        """Delete one dataset's explicit selection atomically, without cascades."""
        if table not in DELETABLE:
            raise ValueError('This record type cannot be deleted here.')
        identifiers = list(dict.fromkeys(identifiers))
        if not identifiers:
            raise ValueError('Select at least one record to delete.')
        self.guard.require('delete')
        key, dependents = DELETABLE[table]
        with self.guard.auth.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                actor = self.guard.auth.require_admin(self.guard.token, cursor)
                from app.database.provenance import source_reference as current_source
                cursor.execute("SELECT set_config('app.actor', %s, true), set_config('app.source', %s, true)",
                               (actor['username'], source_reference if source_reference is not None else current_source()))
                # Consistent lock order avoids deadlocks between overlapping batches.
                for identifier in sorted(identifiers):
                    self._delete_record(cursor, actor, table, key, dependents, identifier)
        return len(identifiers)

    @staticmethod
    def _delete_record(cursor, actor, table, key, dependents, identifier):
        cursor.execute(sql.SQL('SELECT {} FROM {} WHERE {}=%s FOR UPDATE').format(
            sql.Identifier(key), sql.Identifier(table), sql.Identifier(key)), (identifier,))
        if not cursor.fetchone():
            raise ValueError(f'{identifier}: record no longer exists. No records in this batch were deleted.')
        for child, foreign_key in dependents:
            cursor.execute(sql.SQL('SELECT 1 FROM {} WHERE {}=%s LIMIT 1').format(sql.Identifier(child), sql.Identifier(foreign_key)), (identifier,))
            if cursor.fetchone():
                raise ValueError(f'{identifier}: delete dependent records first. No records in this batch were deleted. Automatic cascade deletion is not allowed.')
        if table == 'grading_policy':
            cursor.execute('''SELECT 1 FROM grade g JOIN enrollment e
                ON g.enrollment_id=e.enrollment_id WHERE e.class_id=%s LIMIT 1''', (identifier,))
            if cursor.fetchone():
                raise ValueError(f'{identifier}: delete persisted period results before removing their grading policy. No records in this batch were deleted.')
            cursor.execute('DELETE FROM grade_percentage WHERE class_id=%s', (identifier,))
        cursor.execute(sql.SQL('DELETE FROM {} WHERE {}=%s').format(sql.Identifier(table), sql.Identifier(key)), (identifier,))
        cursor.execute('INSERT INTO security_events(actor_id,action,target) VALUES (%s,%s,%s)',
                       (actor['user_id'], 'record.deleted', f'{table}:{identifier}'))
