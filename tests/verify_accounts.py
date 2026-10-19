"""Called by verify_period_grading inside its isolated, disposable schema."""
from secrets import token_urlsafe
from unittest.mock import MagicMock, patch

from app.services.account_service import AccountService, token_hash
from app.services.access_control import AccessGuard, SecuredService, scope_snapshot
from app.services.record_deletion_service import RecordDeletionService
from app.gui.data_snapshot import load_snapshot


def rejected(operation, expected=PermissionError):
    try:
        operation()
    except expected:
        return
    raise AssertionError('Restricted action was accepted')


def verify_accounts(connect):
    auth = AccountService(connect)
    assert auth.needs_setup()
    admin_password = token_urlsafe(24)
    admin_id = auth.create_account('testadmin', 'Test Admin', admin_password, 'admin', first_admin=True)
    admin = auth.authenticate('testadmin', admin_password)
    assert auth.resolve(admin)['role'] == 'admin'
    rejected(lambda: auth.create_account('bootstrap2', 'No', admin_password, 'admin', first_admin=True))
    rejected(lambda: auth.resolve('invented-session'))
    rejected(lambda: auth.set_active(admin, admin_id, False), ValueError)
    teacher_password = token_urlsafe(24)
    teacher_id = auth.create_account('testteacher', 'Test Teacher', teacher_password, 'teacher', 'T', admin)
    teacher = auth.authenticate('testteacher', teacher_password)
    registrar_id = auth.create_account('testregistrar', 'Test Registrar', teacher_password, 'registrar', token=admin)
    registrar = auth.authenticate('testregistrar', teacher_password)
    rejected(lambda: auth.list_accounts(teacher))
    rejected(lambda: auth.create_account('forbidden', 'No', teacher_password, 'admin', token=teacher))
    guard = AccessGuard(auth, teacher)
    guard.require('scores', ('enrollment', 'E'))
    rejected(lambda: AccessGuard(auth, registrar).require('scores', ('enrollment', 'E')))
    with connect() as connection:
        connection.execute('INSERT INTO teachers VALUES (%s,%s,%s,%s,%s,%s)', ('T2', 'Other', 'Teacher', 'other@example.test', 'CS', 'Active'))
        connection.execute('INSERT INTO class_offerings VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)', ('O2', 'CS-B', 'Monday', 'B', '2026', '1', 'R', 'T2', 'SUB'))
        connection.execute('INSERT INTO grade_percentages VALUES (%s,%s,%s)', ('P2', 100, 'O2'))
        connection.execute('INSERT INTO grade_components VALUES (%s,%s,%s,%s,%s,%s,%s)', ('C2', 'Other exam', 'Exam', 50, '', 'M', 'P2'))
    rejected(lambda: guard.require('grading', ('offering', 'O2')))
    business = MagicMock()
    secured = SecuredService(business, guard)
    rejected(lambda: secured.save_component('C2', 'Moved exam', 'Exam', 50, '', 'M', 'P'))
    rejected(lambda: secured.save_percentage('P2', 100, 'O'))
    business.save_component.assert_not_called()
    business.save_percentage.assert_not_called()
    with patch('app.gui.data_snapshot.get_connection', connect):
        snapshot = scope_snapshot(load_snapshot(), auth.resolve(teacher))
    assert {r[0] for r in snapshot.offerings()} == {'O'}
    assert {r[0] for r in snapshot.teachers()} == {'T'}
    deletion = RecordDeletionService(AccessGuard(auth, admin))
    rejected(lambda: RecordDeletionService(guard).delete('students', 'S'))
    rejected(lambda: deletion.delete('students', 'S'), ValueError)
    deletion.delete('grades', 'G')
    with connect() as connection:
        assert connection.execute('SELECT count(*) FROM grades').fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM security_events WHERE action='record.deleted'").fetchone()[0] == 1
        assert connection.execute('SELECT count(*) FROM grade_component_scores').fetchone()[0] == 2
    # Both deleted rows and their audit entries roll back if a later row fails.
    with connect() as connection:
        for key in ['B1', 'B2']:
            connection.execute('INSERT INTO students (student_id,first_name,last_name,email,program,status) VALUES (%s,%s,%s,%s,%s,%s)',
                               (key, 'Batch', 'Test', key + '@example.test', 'CS', 'Active'))
    rejected(lambda: deletion.delete_many('students', ['B1', 'S']), ValueError)
    rejected(lambda: deletion.delete_many('students', ['B1', 'MISSING']), ValueError)
    with connect() as connection:
        assert connection.execute("SELECT count(*) FROM students WHERE student_id IN ('B1','B2')").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM security_events WHERE target='students:B1'").fetchone()[0] == 0
    assert deletion.delete_many('students', ['B1', 'B2', 'B1']) == 2
    with connect() as connection:
        assert connection.execute("SELECT count(*) FROM students WHERE student_id IN ('B1','B2')").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM security_events WHERE target IN ('students:B1','students:B2')").fetchone()[0] == 2
    rejected(lambda: RecordDeletionService(guard).delete_many('students', ['S']))
    accounts = auth.list_accounts(admin)
    assert not any('password_hash' in row for row in accounts)
    auth.set_active(admin, teacher_id, False)
    rejected(lambda: auth.resolve(teacher))
    auth.set_active(admin, teacher_id, True)
    teacher = auth.authenticate('testteacher', teacher_password)
    auth.change_role(admin, teacher_id, 'dean')
    rejected(lambda: auth.resolve(teacher))
    assert auth.resolve(auth.authenticate('testteacher', teacher_password))['role'] == 'dean'
    rejected(lambda: auth.change_role(admin, admin_id, 'dean'), ValueError)
    for _ in range(5):
        rejected(lambda: auth.authenticate('testteacher', 'wrong test passphrase'), ValueError)
    rejected(lambda: auth.authenticate('testteacher', teacher_password), ValueError)
    auth.logout(registrar)
    rejected(lambda: auth.resolve(registrar))
    with connect() as connection:
        connection.execute('UPDATE account_sessions SET expires_at=CURRENT_TIMESTAMP WHERE token_hash=%s', (token_hash(admin),))
    rejected(lambda: auth.resolve(admin))
    print('Account bootstrap/login, roles, class ownership, upsert protection, scoped reads, audited deletion, role changes, session revocation/expiry and lockout passed.')
