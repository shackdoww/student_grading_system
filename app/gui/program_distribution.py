"""Small, real-data dashboard visualization with interruptible bar animation."""
from collections import Counter
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from app.gui.motion import reduced_motion


def program_counts(students):
    counts = Counter(str(student[4]) for student in students)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 4:
        ranked = ranked[:3] + [('Other programs', sum(count for _, count in ranked[3:]))]
    return ranked


class ProgramDistribution(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(10)
        self.animations = []
        self.set_counts([])

    def set_counts(self, students):
        for animation in self.animations:
            animation.stop()
            animation.deleteLater()
        self.animations = []
        while self.root.count():
            widget = self.root.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        counts = program_counts(students)
        total = sum(count for _, count in counts)
        if not counts:
            label = QLabel('Program breakdown appears when students are loaded.')
            label.setObjectName('subtitle')
            label.setWordWrap(True)
            self.root.addWidget(label)
            return
        colors = ['#3158D4', '#1593CB', '#36A77C', '#8870C7']
        for index, (program, count) in enumerate(counts):
            row = QWidget()
            layout = QVBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            heading = QHBoxLayout()
            label = QLabel(program)
            label.setObjectName('identityTitle')
            label.setWordWrap(True)
            heading.addWidget(label, 1)
            percentage = count / total * 100
            value = QLabel(f'{count} · {percentage:.0f}%')
            value.setObjectName('subtitle')
            heading.addWidget(value)
            layout.addLayout(heading)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setAccessibleName(f'{program}: {count} students, {percentage:.1f} percent')
            bar.setStyleSheet(f'QProgressBar {{background:#EEF2F7;border:0;border-radius:3px;}} '
                             f'QProgressBar::chunk {{background:{colors[index]};border-radius:3px;}}')
            layout.addWidget(bar)
            self.root.addWidget(row)
            target = round(count / total * 1000)
            bar.setValue(0)
            if reduced_motion():
                bar.setValue(target)
            else:
                animation = QPropertyAnimation(bar, b'value', self)
                animation.setDuration(320)
                animation.setStartValue(0)
                animation.setEndValue(target)
                animation.setEasingCurve(QEasingCurve.OutCubic)
                animation.start()
                self.animations.append(animation)
