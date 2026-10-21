"""Navigation stays usable with labels hidden and with restricted accounts."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import app.gui.pyside_app as gui
from app.gui.data_snapshot import DataSnapshot
from tests.ui_helpers import TestAuth as AuthStub


@pytest.fixture
def window(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(gui, 'load_snapshot', DataSnapshot)
    window = gui.StudentHub('test-only-token', AuthStub())
    window.show()
    QTest.qWait(50)
    yield window
    window.close()
    app.processEvents()


def test_compact_navigation_can_expand_without_losing_selected_page(window):
    assert hasattr(window, 'sidebar_toggle'), 'Navigation needs an accessible expand control'
    assert window.sidebar_scroll.width() < 100
    report = window.nav_buttons['reports']
    assert report.accessibleName() == 'Reports'
    assert report.toolTip() == 'Reports'
    assert report.toolButtonStyle() == Qt.ToolButtonIconOnly
    QTest.mouseClick(report, Qt.LeftButton)
    assert window.current_page == 'reports'

    QTest.mouseClick(window.sidebar_toggle, Qt.LeftButton)
    assert window.sidebar_scroll.width() >= 200
    assert report.toolButtonStyle() == Qt.ToolButtonTextBesideIcon
    assert window.current_page == 'reports'
    assert report.isChecked()

    QTest.mouseClick(window.sidebar_toggle, Qt.LeftButton)
    assert window.sidebar_scroll.width() < 100
    report.setFocus()
    QTest.keyClick(report, Qt.Key_Space)
    assert window.current_page == 'reports'
    assert window.output_table.isEnabled()


def test_sidebar_expansion_preserves_role_restrictions(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(gui, 'load_snapshot', DataSnapshot)
    window = gui.StudentHub('test-only-token', AuthStub('teacher'))
    window.show()
    QTest.qWait(50)
    try:
        assert hasattr(window, 'sidebar_toggle'), 'Navigation needs an accessible expand control'
        for _ in range(2):
            QTest.mouseClick(window.sidebar_toggle, Qt.LeftButton)
            assert not window.nav_buttons['import'].isVisible()
            assert 'accounts' not in window.nav_buttons
            assert 'records' not in window.nav_buttons
    finally:
        window.close()
        app.processEvents()


def test_class_schedule_controls_fit_at_dialog_minimum_width():
    from app.gui.academic_editor import RECORDS, RecordDialog
    from app.gui.theme import apply_theme

    app = QApplication.instance() or QApplication([])
    old_palette, old_stylesheet = app.palette(), app.styleSheet()
    apply_theme(app)
    dialog = RecordDialog(None, 'Class', RECORDS['Class Offerings'][2].split(),
                          {'teacher': [], 'subject': []})
    try:
        dialog.resize(dialog.minimumWidth(), dialog.sizeHint().height())
        dialog.show()
        app.processEvents()
        schedule = dialog.inputs['schedule']
        # All weekday and time-block controls must fit inside the dialog when
        # a user resizes it to the minimum permitted width.
        bottom_right = schedule.mapTo(dialog, QPoint(schedule.width() - 1, schedule.height() - 1))
        assert dialog.rect().contains(bottom_right)
    finally:
        dialog.close()
        app.setPalette(old_palette)
        app.setStyleSheet(old_stylesheet)
