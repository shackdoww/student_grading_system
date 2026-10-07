from unittest.mock import MagicMock
import pytest

from app.services.account_service import hash_password, verify_password
from app.services.access_control import allowed, AccessGuard, SecuredService


def test_password_hashes_are_salted_and_verified():
    password = 'a long test passphrase'
    first, second = hash_password(password), hash_password(password)
    assert first != second and password not in first
    assert verify_password(password, first)
    assert not verify_password('a different password', first)
    assert not verify_password(password, 'not-a-hash')
    with pytest.raises(ValueError):
        hash_password('short')


@pytest.mark.parametrize('role,action,expected', [
    ('admin', 'delete', True), ('dean', 'academic', True), ('dean', 'scores', False),
    ('teacher', 'scores', True), ('teacher', 'accounts', False),
    ('registrar', 'enrollments', True), ('registrar', 'grades', False),
    ('unknown', 'students', False)])
def test_role_matrix_denies_unlisted_permissions(role, action, expected):
    assert allowed(role, action) is expected


def test_service_proxy_denies_before_business_write():
    auth = MagicMock()
    auth.resolve.return_value = dict(role='registrar', teacher_id=None)
    business = MagicMock()
    secured = SecuredService(business, AccessGuard(auth, 'token'))
    with pytest.raises(PermissionError):
        secured.record_score('SCORE', 'ENROLLMENT', 'C', 10)
    business.record_score.assert_not_called()
    with pytest.raises(PermissionError):
        secured.unlisted_method()


def test_teacher_scope_checked_against_database_assignment():
    auth = MagicMock()
    auth.resolve.return_value = dict(role='teacher', teacher_id='T1')
    connection = auth.connect.return_value.__enter__.return_value
    guard = AccessGuard(auth, 'token')
    connection.execute.return_value.fetchone.return_value = ('T2',)
    with pytest.raises(PermissionError):
        guard.require('scores', ('enrollment', 'E2'))
    connection.execute.return_value.fetchone.return_value = ('T1',)
    guard.require('scores', ('enrollment', 'E1'))
    with pytest.raises(PermissionError):
        guard.require('scores')


def test_revoked_session_cannot_reach_write():
    auth, business = MagicMock(), MagicMock()
    auth.resolve.side_effect = PermissionError('session revoked')
    secured = SecuredService(business, AccessGuard(auth, 'token'))
    with pytest.raises(PermissionError):
        secured.save('S', 'First', 'Last', 'email', 'CS', 'Active')
    business.save.assert_not_called()


def test_unauthenticated_window_is_not_constructed():
    from PySide6.QtWidgets import QApplication
    from app.gui.pyside_app import StudentHub
    app = QApplication.instance() or QApplication([])
    auth = MagicMock()
    auth.resolve.side_effect = PermissionError('Sign in required')
    with pytest.raises(PermissionError):
        StudentHub(None, auth)


@pytest.mark.parametrize('role', ['dean', 'teacher', 'registrar'])
def test_non_admin_ui_has_no_account_or_deletion_page(monkeypatch, role):
    from PySide6.QtWidgets import QApplication, QPushButton
    import app.gui.pyside_app as gui
    from app.gui.data_snapshot import DataSnapshot
    from tests.ui_helpers import TestAuth
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(gui, 'load_snapshot', DataSnapshot)
    window = gui.StudentHub('test-only-token', TestAuth(role))
    assert 'accounts' not in window.pages and 'records' not in window.pages
    assert window.nav_buttons['import'].isHidden()
    score = next(b for b in window.findChildren(QPushButton) if b.text() == 'Record Score')
    assert score.isEnabled() == (role == 'teacher')
    window.close()
