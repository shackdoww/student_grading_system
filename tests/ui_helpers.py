"""Explicit fake authentication for UI tests, never used by application startup."""
from app.gui.pyside_app import StudentHub


class TestAuth:
    def __init__(self, role='admin'):
        self.role = role

    def resolve(self, token):
        return dict(user_id='test-only', username='test-only', full_name='UI test', role=self.role, teacher_id='T' if self.role == 'teacher' else None)

    def list_accounts(self, token):
        return []


def admin_window():
    return StudentHub('test-only-token', TestAuth())
