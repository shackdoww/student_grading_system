"""Exercise interruption and input delivery, rather than animation implementation details."""
import pytest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QStackedWidget

from app.gui.motion import InteractionFeedback, PageReveal


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_rapid_switches_and_resize_leave_live_page_usable(app):
    stack = QStackedWidget()
    stack.resize(400, 250)
    stack.addWidget(QLabel('First'))
    stack.addWidget(QLabel('Second'))
    motion = PageReveal(stack)
    stack.show()
    app.processEvents()
    for index in (1, 0, 1, 0, 1):
        stack.setCurrentIndex(index)
        motion.reveal()
        QTest.qWait(15)
    stack.resize(450, 280)
    app.processEvents()
    assert not motion.isVisible()
    assert stack.currentIndex() == 1
    motion.reveal()
    QTest.qWait(300)
    assert not motion.isVisible()
    assert stack.currentWidget().isVisible()
    stack.close()


def test_button_feedback_does_not_consume_clicks(app):
    button = QPushButton('Save')
    feedback = InteractionFeedback(button)
    clicks = []
    button.clicked.connect(lambda: clicks.append(True))
    button.show()
    app.processEvents()
    QTest.mouseClick(button, Qt.LeftButton)
    QTest.keyClick(button, Qt.Key_Space)
    assert len(clicks) == 2
    button.setEnabled(False)
    QTest.mouseClick(button, Qt.LeftButton)
    assert len(clicks) == 2
    button.close()


def test_reduced_motion_skips_page_transition(app, monkeypatch):
    monkeypatch.setenv('STUDENT_HUB_REDUCED_MOTION', '1')
    stack = QStackedWidget()
    stack.addWidget(QLabel('Page'))
    motion = PageReveal(stack)
    stack.show()
    app.processEvents()
    motion.reveal()
    assert not motion.isVisible()
    stack.close()
