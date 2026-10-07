import pytest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.gui.window_chrome import BorderlessWindow, TitleBar


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_custom_controls_and_resize_handle_states(app):
    window = BorderlessWindow()
    window.title_bar = TitleBar(window)
    window.title_bar.setGeometry(0, 0, 500, 42)
    window.resize(500, 300)
    window.show()
    app.processEvents()
    assert window.windowFlags() & Qt.FramelessWindowHint
    assert all(handle.isVisible() for handle in window.resize_handles)
    QTest.mouseClick(window.title_bar.maximize, Qt.LeftButton)
    app.processEvents()
    assert window.isMaximized()
    assert window.title_bar.maximize.accessibleName() == 'Restore'
    assert not any(handle.isVisible() for handle in window.resize_handles)
    QTest.mouseClick(window.title_bar.maximize, Qt.LeftButton)
    app.processEvents()
    assert not window.isMaximized()
    assert all(handle.isVisible() for handle in window.resize_handles)
    QTest.mouseClick(window.title_bar.minimize, Qt.LeftButton)
    app.processEvents()
    assert window.isMinimized()
    window.showNormal()
    QTest.mouseDClick(window.title_bar, Qt.LeftButton)
    app.processEvents()
    assert window.isMaximized()
    QTest.mouseClick(window.title_bar.close_button, Qt.LeftButton)
    assert not window.isVisible()
