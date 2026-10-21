from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.accounts import DataRecordsPage
from app.gui.pyside_app import table, fill_table
from app.services.record_deletion_service import RecordDeletionService


@pytest.fixture
def page():
    application = QApplication.instance() or QApplication([])
    app = MagicMock()
    records = {'grade': [dict(grade_id='G1', final_grade=80), dict(grade_id='G2', final_grade=90)],
               'student': [dict(student_id='S1')]}
    app.data.records.return_value = records
    widget = DataRecordsPage(app, table, fill_table)
    widget.kind.setCurrentIndex(widget.kind.findData('grade'))
    yield widget
    widget.close()


def test_checkboxes_select_all_clear_and_refresh(page):
    assert not page.delete_button.isEnabled()
    page.list.item(0, 0).setCheckState(Qt.Checked)
    assert page.checked_keys() == ['G1']
    assert page.selection_count.text() == '1 of 2 selected'
    page.refresh()
    assert page.checked_keys() == ['G1']
    page.select_all.click()
    assert page.checked_keys() == ['G1', 'G2']
    page.clear_selection.click()
    assert not page.checked_keys()
    assert not page.delete_button.isEnabled()
    page.set_checked(True)
    page.kind.setCurrentIndex(page.kind.findData('student'))
    assert not page.checked_keys()  # Never carry selection into another dataset.


def test_confirmation_defaults_to_no_and_cancel_does_not_write(page, monkeypatch):
    page.set_checked(True)

    def cancel(dialog):
        assert dialog.defaultButton().text() in ('&No', 'No')
        assert '2 selected grade' in dialog.text()
        assert dialog.detailedText() == 'G1\nG2'
        assert 'No backup' in dialog.informativeText()
        return QMessageBox.No

    monkeypatch.setattr(QMessageBox, 'exec', cancel)
    page.delete()
    page.app.run_write.assert_not_called()


def test_batch_uses_explicit_checked_keys_not_highlighted_row(page, monkeypatch):
    page.list.item(0, 0).setCheckState(Qt.Checked)
    page.list.setCurrentCell(1, 1)
    monkeypatch.setattr(QMessageBox, 'exec', lambda _: QMessageBox.Yes)
    page.delete()
    operation, message, done = page.app.run_write.call_args.args
    operation()
    page.app.deletion_service.delete_many.assert_called_once_with('grade', ('G1',))
    assert message(1) == '1 record(s) deleted.'
    done(1)
    assert not page.checked_keys()


def test_batch_rejects_empty_or_unlisted_targets_before_connection():
    guard = MagicMock()
    service = RecordDeletionService(guard)
    with pytest.raises(ValueError):
        service.delete_many('grade', [])
    with pytest.raises(ValueError):
        service.delete_many('user_accounts', ['admin'])
    guard.auth.connect.assert_not_called()


def test_batch_checks_admin_before_connection():
    guard = MagicMock()
    guard.require.side_effect = PermissionError('Admin only')
    with pytest.raises(PermissionError):
        RecordDeletionService(guard).delete_many('grade', ['G1'])
    guard.auth.connect.assert_not_called()
