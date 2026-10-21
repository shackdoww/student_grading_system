"""Day/time picker; the displayed rubric schedule is derived from selections."""

from collections import defaultdict
from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QTimeEdit,
    QPushButton,
    QLabel,
)
from app.services.scheduling import normalize_meetings


class ScheduleEditor(QWidget):
    def __init__(self, parent=None, meetings=None, legacy_text=""):
        super().__init__(parent)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.blocks = []
        if legacy_text and not meetings:
            self.root.addWidget(
                QLabel(
                    "Existing schedule: "
                    + legacy_text
                    + "\nSelect explicit days/times to confirm it."
                )
            )
        self.add = QPushButton("Add another time block")
        self.add.clicked.connect(lambda: self.add_block())
        self.root.addWidget(self.add)
        groups = defaultdict(list)
        for row in meetings or []:
            groups[(row["start_time"], row["end_time"])].append(row["weekday"])
        if groups:
            for (start, end), days in groups.items():
                self.add_block(days, start, end)
        else:
            self.add_block()

    def add_block(self, days=(), start=None, end=None):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        weekdays = QHBoxLayout()
        checks = {}
        for day, label in enumerate(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1
        ):
            check = QCheckBox(label)
            check.setChecked(day in days)
            checks[day] = check
            weekdays.addWidget(check)
        layout.addLayout(weekdays)
        times = QHBoxLayout()
        start_edit = QTimeEdit()
        end_edit = QTimeEdit()
        for edit, value, default in [
            (start_edit, start, QTime(9, 0)),
            (end_edit, end, QTime(10, 0)),
        ]:
            edit.setDisplayFormat("h:mm AP")
            edit.setTime(QTime(value.hour, value.minute) if value else default)
        times.addWidget(QLabel("From"))
        times.addWidget(start_edit)
        times.addWidget(QLabel("To"))
        times.addWidget(end_edit)
        remove = QPushButton("Remove block")
        times.addWidget(remove)
        layout.addLayout(times)
        block = (widget, checks, start_edit, end_edit)

        def discard():
            self.blocks.remove(block)
            widget.deleteLater()

        remove.clicked.connect(discard)
        self.blocks.append(block)
        self.root.insertWidget(self.root.count() - 1, widget)

    def values(self):
        return normalize_meetings(
            [
                dict(
                    weekday=day,
                    start_time=start.time().toPython(),
                    end_time=end.time().toPython(),
                )
                for _, checks, start, end in self.blocks
                for day, check in checks.items()
                if check.isChecked()
            ]
        )
