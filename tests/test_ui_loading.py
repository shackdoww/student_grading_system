from time import perf_counter, sleep

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import app.gui.pyside_app as gui
from tests.ui_helpers import admin_window
from app.gui.data_snapshot import DataSnapshot


def wait_until(predicate):
    deadline = perf_counter() + 3
    while not predicate() and perf_counter() < deadline:
        QTest.qWait(10)
    assert predicate()


def test_cached_navigation_and_coalesced_reload(monkeypatch):
    app = QApplication.instance() or QApplication([])
    calls = []

    def loader():
        calls.append(True)
        sleep(0.03)
        return DataSnapshot()

    monkeypatch.setattr(gui, 'load_snapshot', loader)
    window = admin_window()
    window.error = lambda message: (_ for _ in ()).throw(AssertionError(message))
    window.show()
    wait_until(lambda: window._data_version == 1)
    for key in list(window.pages) * 2:
        window.show_page(key)
    assert len(calls) == 1  # Navigation must not touch the database.
    window.reload_data()
    window.reload_data()
    window.reload_data()
    wait_until(lambda: not window._loading)
    assert len(calls) == 3  # One ongoing reload plus one coalesced follow-up.
    assert window._data_version == 2
    window.close()


def test_save_invalidates_snapshot_and_failure_is_visible(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(gui, 'load_snapshot', DataSnapshot)
    window = admin_window()
    window.show()
    messages, warnings, errors = [], [], []
    window.success = messages.append
    window.warning = warnings.append
    window.error = errors.append
    wait_until(lambda: window._data_version == 1)
    window.run_write(lambda: sleep(0.06), 'Saved')
    window.run_write(lambda: None, 'Duplicate')
    wait_until(lambda: window._data_version == 2)
    assert messages == ['Saved']
    assert len(warnings) == 1

    def failed():
        raise ValueError('Rejected by business rules')

    window.run_write(failed, 'Unexpected success')
    wait_until(lambda: bool(errors))
    assert errors == ['Rejected by business rules']
    assert not window._writing
    window.close()


def test_database_load_failure_is_reported(monkeypatch):
    app = QApplication.instance() or QApplication([])

    def failed():
        raise RuntimeError('Database connection unavailable')

    monkeypatch.setattr(gui, 'load_snapshot', failed)
    window = admin_window()
    errors = []
    window.error = errors.append
    window.show()
    wait_until(lambda: bool(errors))
    assert errors == ['Database connection unavailable']
    assert window._data_version == 0
    assert 'Could not' in window.title_bar.status.text()
    window.close()
