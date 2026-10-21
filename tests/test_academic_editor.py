from datetime import date
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.academic_editor import RecordDialog
from app.gui.data_snapshot import DataSnapshot, TABLES
from app.repositories import protected_delete


def test_editor_preserves_identity_and_parses_dates():
    app = QApplication.instance() or QApplication([])
    records = {name: [] for name in TABLES}
    record = dict(period_id='P1', name='Midterm', start_date=date(2026, 1, 1),
                  end_date=date(2026, 2, 1), school_year='2026', semester='1')
    dialog = RecordDialog(None, 'Period', list(record), records, record)
    assert dialog.inputs['period_id'].isReadOnly()
    assert dialog.values()[2] == date(2026, 1, 1)
    dialog.inputs['start_date'].setText('invalid')
    with pytest.raises(ValueError):
        dialog.values()
    dialog.close()


def test_snapshot_editor_data_is_detached():
    snapshot = DataSnapshot()
    snapshot.records()['teacher'].append({'teacher_id': 'new'})
    assert snapshot.records()['teacher'] == []


@pytest.mark.parametrize('referenced', [True, False])
def test_protected_delete_checks_children_before_deleting(monkeypatch, referenced):
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [('C1',), (1,) if referenced else None, None]
    monkeypatch.setattr(protected_delete, 'get_connection', lambda: connection)
    if referenced:
        with pytest.raises(ValueError, match='preserve evidence'):
            protected_delete.delete_unreferenced('grade_component', 'C1')
        assert cursor.execute.call_count == 2
    else:
        protected_delete.delete_unreferenced('grade_component', 'C1')
        assert cursor.execute.call_count == 4
    assert all(call.args[1] == ('C1',) for call in cursor.execute.call_args_list)
