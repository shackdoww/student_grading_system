"""Small, interruptible Qt animations that never move layout-owned widgets."""

import os

from PySide6.QtCore import QEasingCurve, QEvent, Property, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget
from app.gui.theme import ACCENT, BG


def reduced_motion():
    return os.getenv("STUDENT_HUB_REDUCED_MOTION", "").lower() in ("1", "true", "yes")


class PageReveal(QWidget):
    """Animate a snapshot above a live page, keeping its geometry and focus intact."""

    def __init__(self, host):
        super().__init__(host)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self._progress = 1.0
        self._snapshot = None
        self.animation = QPropertyAnimation(self, b"progress", self)
        self.animation.setDuration(220)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.cancel)
        host.installEventFilter(self)
        self.hide()

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = value
        self.update()

    progress = Property(float, get_progress, set_progress)

    def reveal(self):
        self.cancel()
        host = self.parentWidget()
        if reduced_motion() or not host.isVisible() or host.width() <= 0:
            return
        self._snapshot = host.grab()
        self.setGeometry(host.rect())
        self._progress = 0.0
        self.show()
        self.raise_()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def cancel(self):
        self.animation.stop()
        self.hide()
        self._snapshot = None

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Hide):
            self.cancel()
        return False

    def paintEvent(self, event):
        if self._snapshot is None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BG))
        painter.setOpacity(0.4 + 0.6 * self._progress)
        painter.drawPixmap(0, round(10 * (1 - self._progress)), self._snapshot)
        painter.end()


class InteractionFeedback(QWidget):
    """A transparent animated wash for mouse, keyboard focus, and press feedback."""

    def __init__(self, button):
        super().__init__(button)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self._strength = 0.0
        self.animation = QPropertyAnimation(self, b"strength", self)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        button.installEventFilter(self)
        self.setGeometry(button.rect())
        self.show()

    def get_strength(self):
        return self._strength

    def set_strength(self, value):
        self._strength = value
        self.update()

    strength = Property(float, get_strength, set_strength)

    def animate(self, value, duration=140):
        self.animation.stop()
        if reduced_motion():
            self.set_strength(value)
            return
        self.animation.setDuration(duration)
        self.animation.setStartValue(self._strength)
        self.animation.setEndValue(value)
        self.animation.start()

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Resize:
            self.setGeometry(watched.rect())
        elif kind in (QEvent.Enter, QEvent.FocusIn):
            self.animate(0.07)
        elif kind in (QEvent.Leave, QEvent.FocusOut):
            self.animate(0.0)
        elif kind == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.animate(0.16, 70)
        elif kind == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.animate(0.07 if watched.underMouse() else 0.0)
        elif kind == QEvent.KeyPress and event.key() in (Qt.Key_Space, Qt.Key_Return):
            self.animate(0.16, 70)
        elif kind == QEvent.KeyRelease and event.key() in (Qt.Key_Space, Qt.Key_Return):
            self.animate(0.07)
        elif kind in (QEvent.Hide, QEvent.EnabledChange):
            self.animation.stop()
            self.set_strength(0.0)
        return False

    def paintEvent(self, event):
        if not self.parentWidget().isEnabled():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(ACCENT)
        color.setAlphaF(self._strength)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        painter.end()
