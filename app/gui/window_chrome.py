"""Native move/resize behavior with application-drawn window controls."""

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QToolButton, QWidget


def window_icon(kind):
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor('#64748B'), 1.5))
    if kind == 'minimize':
        painter.drawLine(4, 10, 14, 10)
    elif kind == 'maximize':
        painter.drawRect(4, 4, 10, 10)
    elif kind == 'restore':
        painter.drawRect(4, 7, 7, 7)
        painter.drawLine(7, 4, 14, 4)
        painter.drawLine(14, 4, 14, 11)
    else:
        painter.drawLine(5, 5, 13, 13)
        painter.drawLine(13, 5, 5, 13)
    painter.end()
    return QIcon(pixmap)


class ResizeHandle(QWidget):
    def __init__(self, window, edges, cursor):
        super().__init__(window)
        self.edges = edges
        self.setCursor(cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self.window().windowHandle()
            if handle:
                handle.startSystemResize(self.edges)
            event.accept()


class BorderlessWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint
                            | Qt.WindowMinMaxButtonsHint)
        edge_definitions = (
            (Qt.LeftEdge, Qt.SizeHorCursor), (Qt.RightEdge, Qt.SizeHorCursor),
            (Qt.TopEdge, Qt.SizeVerCursor), (Qt.BottomEdge, Qt.SizeVerCursor),
            (Qt.LeftEdge | Qt.TopEdge, Qt.SizeFDiagCursor),
            (Qt.RightEdge | Qt.TopEdge, Qt.SizeBDiagCursor),
            (Qt.LeftEdge | Qt.BottomEdge, Qt.SizeBDiagCursor),
            (Qt.RightEdge | Qt.BottomEdge, Qt.SizeFDiagCursor))
        self.resize_handles = [ResizeHandle(self, edges, cursor) for edges, cursor in edge_definitions]

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def update_handles(self):
        width, height, edge, corner = self.width(), self.height(), 5, 10
        rects = (QRect(0, corner, edge, height - 2 * corner),
                 QRect(width - edge, corner, edge, height - 2 * corner),
                 QRect(corner, 0, width - 2 * corner, edge),
                 QRect(corner, height - edge, width - 2 * corner, edge),
                 QRect(0, 0, corner, corner), QRect(width - corner, 0, corner, corner),
                 QRect(0, height - corner, corner, corner),
                 QRect(width - corner, height - corner, corner, corner))
        for handle, rect in zip(self.resize_handles, rects):
            handle.setGeometry(rect)
            handle.setVisible(not self.isMaximized() and not self.isFullScreen())
            handle.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_handles()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            self.update_handles()
            if hasattr(self, 'title_bar'):
                self.title_bar.update_maximize_icon()


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName('titleBar')
        self.setFixedHeight(42)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 4, 6, 4)
        layout.setSpacing(8)
        title = QLabel('Student Hub')
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        title.setObjectName('windowTitle')
        layout.addWidget(title)
        self.status = QLabel('Loading school data…')
        self.status.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.status.setObjectName('loadStatus')
        layout.addWidget(self.status)
        layout.addStretch()
        self.minimize = self.control('Minimize', 'minimize', window.showMinimized)
        self.maximize = self.control('Maximize', 'maximize', window.toggle_maximized)
        self.close_button = self.control('Close', 'close', window.close)
        self.close_button.setObjectName('windowClose')
        for control in (self.minimize, self.maximize, self.close_button):
            layout.addWidget(control)

    def control(self, label, icon, action):
        button = QToolButton(self)
        button.setFixedSize(34, 30)
        button.setIcon(window_icon(icon))
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.clicked.connect(action)
        return button

    def update_maximize_icon(self):
        maximized = self.window().isMaximized()
        self.maximize.setIcon(window_icon('restore' if maximized else 'maximize'))
        label = 'Restore' if maximized else 'Maximize'
        self.maximize.setToolTip(label)
        self.maximize.setAccessibleName(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.window().windowHandle():
            self.window().windowHandle().startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window().toggle_maximized()
            event.accept()
