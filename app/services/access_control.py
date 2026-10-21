"""Permission checks at the application boundary, not just hidden UI buttons."""


PERMISSIONS = {
    'admin': {'student', 'enrollment', 'academic', 'grading', 'scores', 'grade', 'import', 'delete', 'accounts'},
    'dean': {'academic', 'grading'},
    'teacher': {'grading', 'scores', 'grade'},
    'registrar': {'student', 'enrollment'},
}


def allowed(role, action):
    return action in PERMISSIONS.get(role, set())


def scope_snapshot(snapshot, account):
    from app.gui.data_snapshot import DataSnapshot
    if account['role'] == 'admin':
        return snapshot
    records = snapshot.records()
    records['audit_log'] = []
    if account['role'] != 'teacher':
        return DataSnapshot(records)
    offerings = [r for r in records['class'] if r['teacher_id'] == account['teacher_id']]
    oids = {r['class_id'] for r in offerings}
    enrollments = [r for r in records['enrollment'] if r['class_id'] in oids]
    eids = {r['enrollment_id'] for r in enrollments}
    sids = {r['student_id'] for r in enrollments}
    subject_ids = {r['subject_id'] for r in offerings}
    records['class'] = offerings
    records['enrollment'] = enrollments
    records['student'] = [r for r in records['student'] if r['student_id'] in sids]
    records['teacher'] = [r for r in records['teacher'] if r['teacher_id'] == account['teacher_id']]
    records['subject'] = [r for r in records['subject'] if r['subject_id'] in subject_ids]
    records['grade_percentage'] = [r for r in records['grade_percentage'] if r['class_id'] in oids]
    records['grade_component_score']=[r for r in records['grade_component_score'] if r['enrollment_id'] in eids]
    records['grade']=[r for r in records['grade'] if r['enrollment_id'] in eids]
    records['grading_policy']=[r for r in records['grading_policy'] if r['class_id'] in oids]
    return DataSnapshot(records)


class AccessGuard:
    def __init__(self, auth, token):
        self.auth, self.token = auth, token

    def require(self, action, resource=None):
        account = self.auth.resolve(self.token)
        if not allowed(account['role'], action):
            raise PermissionError('Your role does not permit this action.')
        if account['role'] == 'teacher':
            if resource is None:
                raise PermissionError('A class assignment is required.')
            kind, identifier, *options = resource
            queries = {
                'offering': 'SELECT teacher_id FROM class WHERE class_id=%s',
                'enrollment': 'SELECT o.teacher_id FROM enrollment e JOIN class o ON e.class_id=o.class_id WHERE e.enrollment_id=%s',
                'percentage': 'SELECT o.teacher_id FROM grade_percentage p JOIN class o ON p.class_id=o.class_id WHERE p.percentage_id=%s',
            }
            with self.auth.connect() as connection:
                row = connection.execute(queries[kind], (identifier,)).fetchone()
                if row is None and options == [True]:
                    return account
                if not row or row[0] != account['teacher_id']:
                    raise PermissionError('You may only change classes assigned to your teacher record.')
        return account


RULES = {
    'save': ('student', None), 'create': ('student', None), 'enroll': ('enrollment', None),
    'update_status': ('enrollment', None),
    'record_score': ('scores', lambda args, kw: ('enrollment', args[1])),
    'calculate_and_save': ('grade', lambda args, kw: ('enrollment', args[0])),
    'save_policy': ('grading', lambda args, kw: ('offering', args[0]['class_id'])),
    'save_teacher': ('academic', None), 'create_teacher': ('academic', None), 'save_subject': ('academic', None),
    'save_offering': ('academic', None), 'save_period': ('academic', None),
    'save_component': ('academic', None),
    'delete_unreferenced': ('delete', None), 'import_all': ('import', None),
}


class SecuredService:
    def __init__(self, service, guard, overrides=None):
        self._service, self._guard = service, guard
        self._rules = dict(RULES, **(overrides or {}))

    def __getattr__(self, name):
        if name not in self._rules:
            raise PermissionError('This operation is not exposed to signed-in users.')
        action, target = self._rules[name]
        def call(*args, **kwargs):
            from app.database.provenance import source_reference
            reference = kwargs.pop('source_reference', None)
            if reference is None:
                reference = source_reference()
            account = self._guard.require(action, target(args, kwargs) if target else None)
            from app.database.connection import audit_actor
            from app.database.provenance import write_source
            with audit_actor(account['username']), write_source(reference):
                return getattr(self._service, name)(*args, **kwargs)
        return call
