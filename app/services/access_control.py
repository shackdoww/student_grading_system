"""Permission checks at the application boundary, not just hidden UI buttons."""


PERMISSIONS = {
    'admin': {'students', 'enrollments', 'academic', 'grading', 'scores', 'grades', 'import', 'delete', 'accounts'},
    'dean': {'academic', 'grading'},
    'teacher': {'grading', 'scores', 'grades'},
    'registrar': {'students', 'enrollments'},
}


def allowed(role, action):
    return action in PERMISSIONS.get(role, set())


def scope_snapshot(snapshot, account):
    from app.gui.data_snapshot import DataSnapshot
    if account['role'] != 'teacher':
        return snapshot
    records = snapshot.records()
    offerings = [r for r in records['class_offerings'] if r['teacher_id'] == account['teacher_id']]
    oids = {r['offering_id'] for r in offerings}
    enrollments = [r for r in records['enrollments'] if r['offering_id'] in oids]
    eids = {r['enrollment_id'] for r in enrollments}
    sids = {r['student_id'] for r in enrollments}
    subject_ids = {r['subject_id'] for r in offerings}
    records['class_offerings'] = offerings
    records['enrollments'] = enrollments
    records['students'] = [r for r in records['students'] if r['student_id'] in sids]
    records['teachers'] = [r for r in records['teachers'] if r['teacher_id'] == account['teacher_id']]
    records['subjects'] = [r for r in records['subjects'] if r['subject_id'] in subject_ids]
    records['grade_percentages'] = [r for r in records['grade_percentages'] if r['offering_id'] in oids]
    pids = {r['percentage_id'] for r in records['grade_percentages']}
    records['grade_components'] = [r for r in records['grade_components'] if r['percentage_id'] in pids]
    cids = {r['component_id'] for r in records['grade_components']}
    records['grade_component_scores'] = [r for r in records['grade_component_scores'] if r['enrollment_id'] in eids and r['component_id'] in cids]
    for name in ['grades', 'period_grade_results']:
        records[name] = [r for r in records[name] if r['enrollment_id'] in eids]
    for name in ['grading_policies', 'period_category_weights']:
        records[name] = [r for r in records[name] if r['offering_id'] in oids]
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
                'offering': 'SELECT teacher_id FROM class_offerings WHERE offering_id=%s',
                'enrollment': 'SELECT o.teacher_id FROM enrollments e JOIN class_offerings o ON e.offering_id=o.offering_id WHERE e.enrollment_id=%s',
                'percentage': 'SELECT o.teacher_id FROM grade_percentages p JOIN class_offerings o ON p.offering_id=o.offering_id WHERE p.percentage_id=%s',
                'component': 'SELECT o.teacher_id FROM grade_components c JOIN grade_percentages p ON c.percentage_id=p.percentage_id JOIN class_offerings o ON p.offering_id=o.offering_id WHERE c.component_id=%s',
            }
            with self.auth.connect() as connection:
                row = connection.execute(queries[kind], (identifier,)).fetchone()
                if row is None and options == [True]:
                    return account
                if not row or row[0] != account['teacher_id']:
                    raise PermissionError('You may only change classes assigned to your teacher record.')
        return account


RULES = {
    'save': ('students', None), 'enroll': ('enrollments', None),
    'record_score': ('scores', lambda args, kw: ('enrollment', args[1])),
    'calculate_and_save_grade': ('grades', lambda args, kw: ('enrollment', args[0])),
    'calculate_and_save': ('grades', lambda args, kw: ('enrollment', args[0])),
    'save_policy': ('grading', lambda args, kw: ('offering', args[0]['offering_id'])),
    'save_teacher': ('academic', None), 'save_subject': ('academic', None),
    'save_offering': ('academic', None), 'save_period': ('academic', None),
    'save_percentage': ('grading', lambda args, kw: ('offering', args[2])),
    'save_component': ('grading', lambda args, kw: ('percentage', args[6])),
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
            self._guard.require(action, target(args, kwargs) if target else None)
            if name in ['save_component', 'save_percentage']:
                # An upsert must authorize the existing owner as well as the
                # proposed destination, or a guessed ID could move another class's record.
                kind = 'component' if name == 'save_component' else 'percentage'
                self._guard.require(action, (kind, args[0], True))
            return getattr(self._service, name)(*args, **kwargs)
        return call
