from datetime import date
import os
import sys
from uuid import uuid4

from PySide6.QtCore import Qt, QSize, QByteArray, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QPushButton,
    QToolButton, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QScrollArea, QTabWidget, QAbstractItemView, QSizePolicy
)

from app.gui.table_output import export_table, print_table
from app.gui.checklist_reports import class_report, student_report, saved_result
from app.gui.motion import InteractionFeedback, PageReveal
from app.gui.background import BackgroundJobs
from app.gui.data_snapshot import DataSnapshot, load_snapshot
from app.gui.window_chrome import BorderlessWindow, TitleBar

from app.services.enrollment_service import EnrollmentService
from app.services.school_data_import_service import SchoolDataImportService, DATASETS
from app.services.score_service import ScoreService
from app.services.student_service import StudentService
from app.services.academic_service import AcademicService
from app.gui.academic_editor import add_editor_actions
from app.gui.period_grading_dialog import PeriodPolicyDialog
from app.gui.program_distribution import ProgramDistribution
from app.gui.accounts import LoginDialog, AccountsPage, DataRecordsPage
from app.services.account_service import AccountService, ROLES
from app.services.access_control import AccessGuard, SecuredService, allowed, scope_snapshot
from app.services.record_deletion_service import RecordDeletionService
from app.services.period_grading_service import PeriodGradingService


from app.gui.theme import (
    ACCENT, ACCENT_SOFT, DANGER, MUTED, ON_ACCENT, STYLE, WARNING, apply_theme,
)

ENROLLMENT_ROLE = Qt.UserRole + 1


ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")

def sidebar_icon(name, color, size=22):
    path = os.path.join(ICON_DIR, name)
    try:
        with open(path, "r", encoding="utf-8") as file:
            svg = file.read().replace("currentColor", color).encode("utf-8")
        renderer = QSvgRenderer(QByteArray(svg))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except (OSError, RuntimeError):
        return QIcon()


def styled_label(text, object_name):
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def button(text, callback, primary=False, compact=False):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(callback)
    b.setProperty("primary", primary)
    b.setProperty("compact", compact)
    b.motion_feedback = InteractionFeedback(b)
    return b


class Card(QFrame):
    def __init__(self, parent=None, accent=None):
        super().__init__(parent)
        self.setObjectName("card")
        if accent:
            self.setProperty("accent", accent)


class StatCard(Card):
    def __init__(self, label, value, accent, parent=None):
        super().__init__(parent, accent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(4)
        top = QHBoxLayout()
        title = QLabel(label)
        self.setObjectName("statCard")
        title.setObjectName("eyebrow")
        dot = QLabel()
        dot.setObjectName('statIcon')
        dot.setFixedSize(42, 42)
        dot.setAlignment(Qt.AlignCenter)
        dot.setStyleSheet(f'QLabel#statIcon {{background:{ACCENT_SOFT};border-radius:14px;}}')
        icon_name = {"Students": "users-round.svg", "Enrollments": "file-text.svg",
                     "Teachers": "graduation-cap.svg", "Class Offerings": "book-open.svg"}.get(label, "chart.svg")
        dot.setPixmap(sidebar_icon(icon_name, ACCENT, 24).pixmap(24, 24))
        top.addWidget(title)
        top.addStretch()
        top.addWidget(dot)
        layout.addLayout(top)
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        layout.addWidget(self.value)

    def setValue(self, value):
        self.value.setText(str(value))


class PageHeader(QWidget):
    """Shared title treatment for every workspace page."""
    def __init__(self, title, subtitle, action=None, parent=None):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        copy = QVBoxLayout()
        copy.setSpacing(3)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        copy.addWidget(heading)
        description = QLabel(subtitle)
        description.setObjectName("subtitle")
        description.setWordWrap(True)
        copy.addWidget(description)
        layout.addLayout(copy, 1)
        if action:
            layout.addWidget(action, 0, Qt.AlignTop)


def table(columns, rows=0):
    t = QTableWidget(rows, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setDefaultSectionSize(44)
    t.horizontalHeader().setMinimumSectionSize(90)
    t.horizontalHeader().setMaximumSectionSize(260)
    t.setMinimumHeight(160)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setStretchLastSection(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    for column in range(len(columns)):
        widths = {"Program": 105, "Status": 100, "Units": 90, "Section": 100, "Email": 220}
        t.setColumnWidth(column, widths.get(columns[column], 110 if column == 0 else 170))
    t.horizontalHeader().setSectionResizeMode(len(columns) - 1, QHeaderView.Stretch)
    t.setShowGrid(False)
    return t


def fill_table(t, rows):
    blocked = t.blockSignals(True)
    t.setUpdatesEnabled(False)
    t.clearSelection()
    t.setRowCount(len(rows))
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            item = QTableWidgetItem("" if value is None else str(value))
            item.setData(Qt.UserRole, value)
            heading = t.horizontalHeaderItem(c)
            if heading and heading.text().lower() in ('status', 'remarks'):
                status_color = {
                    'Active': ACCENT, 'Enrolled': ACCENT, 'Passed': ACCENT,
                    'Inactive': DANGER, 'Dropped': DANGER, 'Failed': DANGER,
                    'Incomplete': WARNING,
                }.get(str(value))
                if status_color:
                    item.setForeground(QColor(status_color))
            t.setItem(r, c, item)
    t.setUpdatesEnabled(True)
    t.blockSignals(blocked)


def apply_report(widget, report):
    widget.setColumnCount(len(report['headers']))
    widget.setHorizontalHeaderLabels(report['headers'])
    widget.setProperty('outputTitle',report['title'])
    widget.setProperty('reportMetadata',report['metadata'])
    widget.setProperty('reportSummary',report['summary'])
    fill_table(widget,report['rows'])
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    for column,label in enumerate(report['headers']):
        widget.setColumnWidth(column,{'No.':58,'Student':220,'Student Name':240,'Course':100,'MG':100,'FG':100,
                                     'Subject Code':120,'Description':300,'Teacher':170,'Units':80,'F Grade':140}.get(label,140))
    widget.horizontalHeader().setSectionResizeMode(1 if len(report['headers'])<6 else 2,QHeaderView.Stretch)
    widget.resizeRowsToContents()


class StudentDialog(QDialog):
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.setWindowTitle("Student")
        self.setMinimumWidth(430)
        form = QFormLayout(self)
        form.setContentsMargins(26, 24, 26, 18)
        form.setSpacing(12)
        self.fields = {}
        labels = [
            ("Student ID", "student_id"), ("First Name", "first_name"),
            ("Last Name", "last_name"), ("Email", "email"),
            ("Program", "program"), ("Status", "status"), ("Year Level (1–6)", "year_level")
        ]
        for label, key in labels:
            w = QLineEdit()
            self.fields[key] = w
            form.addRow(label, w)
        if student:
            for i, key in enumerate(self.fields):
                self.fields[key].setText(str(student[i]) if i < len(student) and student[i] is not None else '')
            self.fields['student_id'].setReadOnly(True)
        else:
            self.fields["status"].setText("Active")
            self.fields['year_level'].setText('1')
        self.fields['email'].setPlaceholderText('Optional')
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        for control in buttons.buttons():
            control.motion_feedback = InteractionFeedback(control)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return {key: w.text().strip() for key, w in self.fields.items()}


class ScoreDialog(QDialog):
    def __init__(self, parent, enrollment_id, components, scores=None):
        super().__init__(parent)
        self.setWindowTitle("Record Score")
        self.setMinimumWidth(460)
        form = QFormLayout(self)
        form.setContentsMargins(26, 24, 26, 18)
        self.score_id = 'SC-' + uuid4().hex
        self.component = QComboBox()
        for row in components:
            self.component.addItem(f"{row[1]}  ·  max {float(row[3]):g}", row[0])
        self.score = QLineEdit()
        self.remarks = QLineEdit()
        form.addRow("Component", self.component)
        form.addRow("Score", self.score)
        form.addRow("Remarks", self.remarks)
        self.saved_scores = {s['component_id']:s for s in (scores or [])}
        self.delete_requested = False
        self.delete_control = QPushButton('Delete saved score')
        self.delete_control.clicked.connect(self.request_delete)
        self.delete_control.setVisible(bool(parent and getattr(parent, 'app', None) and parent.app.can('delete')))
        form.addRow(self.delete_control)
        self.component.currentIndexChanged.connect(self.load_saved)
        self.load_saved()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        for control in buttons.buttons():
            control.motion_feedback = InteractionFeedback(control)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def load_saved(self):
        saved = self.saved_scores.get(self.component.currentData())
        self.score_id = saved['score_id'] if saved else 'SC-' + uuid4().hex
        self.score.setText(str(saved['score']) if saved else '')
        self.remarks.setText(saved.get('remarks') or '' if saved else '')
        self.delete_control.setEnabled(saved is not None)

    def request_delete(self):
        if QMessageBox.question(self, 'Delete score', 'Delete this saved score? Its grade will be incomplete until you re-enter the score and recompute.') == QMessageBox.Yes:
            self.delete_requested = True
            self.accept()

    def values(self):
        return self.score_id, self.component.currentData(), self.score.text().strip(), self.remarks.text().strip()


class DashboardPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.selected_student = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)

        root.addWidget(PageHeader("Dashboard", "School activity and student performance at a glance.",
                                  button("Add student", self.add_student, True)))

        stats = QGridLayout()
        stats.setSpacing(14)
        self.students_stat = StatCard("Students", "0", ACCENT)
        self.enrollments_stat = StatCard("Enrollments", "0", "#1593CB")
        self.teachers_stat = StatCard("Teachers", "0", "#36A77C")
        self.classes_stat = StatCard("Class Offerings", "0", "#8870C7")
        for i, card in enumerate([self.students_stat, self.enrollments_stat, self.teachers_stat, self.classes_stat]):
            stats.addWidget(card, 0, i)
        root.addLayout(stats)

        workspace = QHBoxLayout()
        workspace.setSpacing(16)

        students_card = Card()
        sl = QVBoxLayout(students_card)
        sl.setContentsMargins(18, 18, 18, 18)
        sh = QHBoxLayout()
        st = QLabel("Students")
        st.setObjectName("cardTitle")
        sh.addWidget(st)
        sh.addStretch()
        refresh = button("", self.app.reload_data, False, True)
        refresh.setIcon(sidebar_icon('refresh-cw.svg', MUTED))
        refresh.setToolTip('Refresh school data')
        refresh.setAccessibleName('Refresh school data')
        refresh.setFixedWidth(42)
        sh.addWidget(refresh)
        sl.addLayout(sh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, ID, program…")
        self.search.textChanged.connect(self.filter_students)
        sl.addWidget(self.search)
        self.student_table = table(["ID", "Name", "Program", "Status"])
        self.student_table.itemSelectionChanged.connect(self.student_selected)
        self.student_table.doubleClicked.connect(self.edit_student)
        sl.addWidget(self.student_table, 1)
        workspace.addWidget(students_card, 2)

        side = QVBoxLayout()
        side.setSpacing(16)
        selected = Card()
        il = QVBoxLayout(selected)
        il.setContentsMargins(20, 20, 20, 20)
        il.addWidget(styled_label("SELECTED STUDENT", "eyebrow"))
        self.student_badge = QLabel('SH')
        self.student_badge.setFixedSize(40, 40)
        self.student_badge.setAlignment(Qt.AlignCenter)
        self.student_badge.setStyleSheet(f'background:{ACCENT_SOFT};color:{ACCENT};border-radius:12px;font-weight:700;')
        il.addWidget(self.student_badge)
        self.selected_name = QLabel("Select a student")
        self.selected_name.setObjectName("cardTitle")
        il.addWidget(self.selected_name)
        self.selected_info = QLabel("Choose a student from the list to view their academic snapshot.")
        self.selected_info.setObjectName("subtitle")
        self.selected_info.setWordWrap(True)
        il.addWidget(self.selected_info)
        self.grade_label = QLabel("—")
        self.grade_label.setObjectName("heroGrade")
        il.addWidget(styled_label('Latest term grade weighted average', 'subtitle'))
        il.addWidget(self.grade_label)
        self.enrollment_label = QLabel("No enrollment selected")
        self.enrollment_label.setObjectName("subtitle")
        il.addWidget(self.enrollment_label)
        il.addStretch()
        side.addWidget(selected, 2)

        quick = QWidget()
        ql = QVBoxLayout(quick)
        ql.setContentsMargins(0, 0, 0, 0)
        quick_grid = QGridLayout()
        quick_grid.addWidget(button("Class Grades", lambda: self.app.show_page("grade"), compact=True), 0, 0)
        quick_grid.addWidget(button("Academic", lambda: self.app.show_page("academic"), compact=True), 0, 1)
        quick_grid.addWidget(button("Enrollments", lambda: self.app.show_page("enrollment"), compact=True), 0, 2)
        quick_grid.addWidget(button("Report", self.open_report, compact=True), 0, 3)
        quick_grid.addWidget(button('Edit student', self.edit_student, compact=True), 1, 0, 1, 2)
        quick_grid.addWidget(button('Delete student', self.delete_student, compact=True), 1, 2, 1, 2)
        ql.addLayout(quick_grid)
        sl.insertWidget(sl.indexOf(self.student_table), quick)
        programs = Card()
        program_layout = QVBoxLayout(programs)
        program_layout.setContentsMargins(20, 16, 20, 16)
        program_layout.addWidget(styled_label('PROGRAM DISTRIBUTION', 'eyebrow'))
        self.program_distribution = ProgramDistribution()
        program_layout.addWidget(self.program_distribution)
        side.addWidget(programs)
        workspace.addLayout(side, 1)
        root.addLayout(workspace, 1)

    def refresh(self):
        try:
            students = self.app.data.students()
            self._students = students
            self.program_distribution.set_counts(students)
            self.filter_students()
            self.students_stat.setValue(len(students))
            self.enrollments_stat.setValue(self.app.enrollment_repo_count())
            self.teachers_stat.setValue(len(self.app.data.teachers()))
            offerings = self.app.data.offerings()
            self.classes_stat.setValue(len(offerings))
            if self.student_table.rowCount() and not self.student_table.selectedItems():
                self.student_table.selectRow(0)
        except Exception as e:
            self.app.error(str(e))

    def filter_students(self):
        query = self.search.text().casefold().strip()
        students = [s for s in getattr(self, "_students", [])
                    if not query or query in " ".join(map(str, s)).casefold()]
        fill_table(self.student_table, [(s[0], f"{s[1]} {s[2]}", s[4], s[5]) for s in students])
        if students:
            index = next((i for i, student in enumerate(students) if student[0] == self.selected_student), 0)
            self.student_table.selectRow(index)
        else:
            self.selected_student = None
            self.selected_name.setText("No student selected")
            self.student_badge.setText('SH')
            self.selected_info.setText("Add a student or adjust your search.")
            self.grade_label.setText("—")
            self.enrollment_label.setText("No enrollment selected")

    def student_selected(self):
        rows = self.student_table.selectedItems()
        if not rows:
            return
        sid = self.student_table.item(self.student_table.currentRow(), 0).text()
        try:
            student = self.app.data.student(sid)
            self.selected_student = sid
            self.selected_name.setText(f"{student[1]} {student[2]}")
            self.student_badge.setText((student[1][:1] + student[2][:1]).upper())
            self.selected_info.setText(f"{student[0]}  ·  {student[4]}  ·  Year {student[6] or 'not entered'}  ·  {student[5]}")
            enrollments = self.app.data.enrollments_for_student(sid)
            self.enrollment_label.setText(f"{len(enrollments)} enrollment(s)")
            terms = sorted({(e[7], e[8]) for e in enrollments}, reverse=True)
            summary = student_report(self.app.data, sid, *terms[0])['summary'][-1].split(': ',1)[1] if terms else '—'
            self.grade_label.setText(summary)
        except Exception as e:
            self.app.error(str(e))

    def add_student(self):
        d = StudentDialog(self)
        if d.exec() != QDialog.Accepted:
            return
        try:
            v = d.values()
            self.app.run_write(lambda: self.app.student_service.create(**v), "Student saved.")
        except Exception as e:
            self.app.error(str(e))

    def edit_student(self, *_):
        if not self.app.can('student') or not self.selected_student:
            return
        dialog = StudentDialog(self, self.app.data.student(self.selected_student))
        if dialog.exec() == QDialog.Accepted:
            values = dialog.values()
            self.app.run_write(lambda: self.app.student_service.save(**values), 'Student updated.')

    def delete_student(self):
        if not self.app.can('delete') or not self.selected_student:
            return
        sid = self.selected_student
        if QMessageBox.question(self, 'Delete student', f'Delete {sid}? Students with enrollments are protected.') == QMessageBox.Yes:
            self.app.run_write(lambda: self.app.deletion_service.delete('student',sid),'Student deleted.')

    def open_report(self):
        if not self.selected_student:
            self.app.warning("Select a student first.")
            return
        self.app.show_page("reports")
        index = self.app.reports.student.findData(self.selected_student)
        self.app.reports.student.setCurrentIndex(index)
        self.app.reports.load_student(self.selected_student)


class AcademicPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        root.addWidget(PageHeader("Academic", "Teachers, subjects, grading periods and class offerings.", button("Refresh", self.app.reload_data)))
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tab_motion = PageReveal(self.tabs)
        self.tabs.currentChanged.connect(lambda: self.tab_motion.reveal())
        root.addWidget(self.tabs, 1)

        self.teacher_table = table(["ID", "Name", "Email", "Department", "Status"])
        self.subject_table = table(["ID", "Code", "Subject", "Units", "Description"])
        self.period_table = table(["ID", "Name", "Start", "End", "School Year", "Semester", "Order"])
        self.offering_table = table(["ID", "Class", "Subject", "Section", "Schedule", "Teacher", "Room"])
        self.weight_table = table(["ID", "Percentage", "Class ID", "Component ID"])
        self.component_table = table(["ID", "Name", "Type", "Maximum", "Description", "Period ID"])
        for name, t in [("Teachers", self.teacher_table), ("Subjects", self.subject_table),
                        ("Grading Periods", self.period_table), ("Class Offerings", self.offering_table),
                        ("Weights", self.weight_table), ("Components", self.component_table)]:
            card = Card()
            l = QVBoxLayout(card)
            l.setContentsMargins(14, 14, 14, 14)
            if name == 'Weights':
                l.addWidget(button('Configure class weights in Class Grades → Period Setup', lambda: self.app.show_page('grade')))
            else:
                add_editor_actions(l, self.app, name, t)
            t.setProperty('outputTitle', name)
            l.addWidget(t)
            self.tabs.addTab(card, name)

    def refresh(self):
        try:
            teachers = self.app.data.teachers()
            fill_table(self.teacher_table, [(r[0], f"{r[1]} {r[2]}", r[3], r[4], r[5]) for r in teachers])
            subjects = self.app.data.subjects()
            fill_table(self.subject_table, [(r[0], r[1], r[2], r[4], r[3] or "—") for r in subjects])
            periods = self.app.data.periods()
            fill_table(self.period_table, [list(r) for r in periods])
            offerings = self.app.data.offerings()
            records = self.app.data.records()
            fill_table(self.weight_table, [(r['percentage_id'], r['percentage'], r['class_id'], r['component_id']) for r in records['grade_percentage']])
            fill_table(self.component_table, [(r[k] for k in 'component_id name type max_score description period_id'.split()) for r in records['grade_component']])
            fill_table(self.offering_table, [(r[0], r[1], r[11] + " — " + r[12], r[3], r[2], f"{r[8]} {r[9]}", r[6] or "—") for r in offerings])
        except Exception as e:
            self.app.error(str(e))


class EnrollmentsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        root.addWidget(PageHeader("Enrollments", "Connect student to class offerings without leaving the workspace.", button("Refresh", self.app.reload_data)))

        editor = Card()
        form = QGridLayout(editor)
        form.setContentsMargins(18, 18, 18, 18)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.addWidget(styled_label("STUDENT", "eyebrow"), 0, 0)
        form.addWidget(styled_label("CLASS OFFERING", "eyebrow"), 0, 1)
        self.student = QComboBox()
        self.offering = QComboBox()
        form.addWidget(self.student, 1, 0)
        form.addWidget(self.offering, 1, 1)
        form.addWidget(styled_label("STATUS", "eyebrow"), 2, 0)
        self.status = QComboBox()
        self.status.addItems(["Enrolled", "Dropped", "Completed"])
        form.addWidget(self.status, 3, 0)
        save = button("Enroll Student", self.save, True)
        form.addWidget(save, 4, 1, Qt.AlignRight)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)
        root.addWidget(editor)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 14, 14, 14)
        l.addWidget(styled_label("Current enrollment roster", "cardTitle"))
        actions = QHBoxLayout()
        actions.addWidget(button('Update selected status', self.update_status))
        actions.addWidget(button('Remove selected enrollment', self.remove_enrollment))
        l.addLayout(actions)
        self.list = table(["Student Number", "Student", "Class", "Section", "Program", "Status"])
        l.addWidget(self.list)
        root.addWidget(card, 1)
        self.refresh()

    def refresh(self):
        try:
            students = self.app.data.students()
            offerings = self.app.data.offerings()
            selected_student = self.student.currentData()
            selected_offering = self.offering.currentData()
            self.student.clear()
            for s in students:
                self.student.addItem(f"{s[0]} · {s[1]} {s[2]}", s[0])
            self.offering.clear()
            for o in offerings:
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]}", o[0])
            for combo, selected in ((self.student, selected_student), (self.offering, selected_offering)):
                index = combo.findData(selected)
                if index >= 0:
                    combo.setCurrentIndex(index)
            rows = []
            self.enrollment_keys = []
            for o in offerings:
                for e in self.app.data.enrollments_for_offering(o[0]):
                    rows.append((e[1], f"{e[2]} {e[3]}", o[1], o[3], e[4], e[5]))
                    self.enrollment_keys.append(e[0])
            fill_table(self.list, rows)
        except Exception as e:
            self.app.error(str(e))

    def update_status(self):
        row = self.list.currentRow()
        if row < 0:
            self.app.warning('Select an enrollment first.')
            return
        eid, status = self.enrollment_keys[row], self.status.currentText()
        self.app.run_write(lambda: self.app.enrollment_service.update_status(eid,status),'Enrollment status updated.')

    def remove_enrollment(self):
        row = self.list.currentRow()
        if row < 0:
            self.app.warning('Select an enrollment first.')
            return
        eid = self.enrollment_keys[row]
        if QMessageBox.question(self,'Remove enrollment','Remove this enrollment? Enrollments with scores or saved grade are protected.') == QMessageBox.Yes:
            self.app.run_write(lambda: self.app.deletion_service.delete('enrollment',eid),'Enrollment removed.')

    def save(self):
        if not self.student.currentData() or not self.offering.currentData():
            self.app.warning('Choose a student and a class offering first.')
            return
        try:
            args = (self.student.currentData(), self.offering.currentData(), self.status.currentText())
            self.app.run_write(lambda: self.app.enrollment_service.enroll(*args), "Student enrolled.")
        except Exception as e:
            self.app.error(str(e))


class GradesPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.current_offering = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        actions = QWidget()
        header = QHBoxLayout(actions)
        header.setContentsMargins(0, 0, 0, 0)
        self.offering = QComboBox()
        self.offering.currentIndexChanged.connect(self.load_class)
        header.addWidget(self.offering)
        root.addWidget(PageHeader("Class Grades", "Select a class, inspect its roster, and record scores.", actions))

        self.summary = QHBoxLayout()
        self.count = StatCard("Students", "0", ACCENT)
        self.average = StatCard("Class Average", "—", "#55BE8C")
        self.summary.addWidget(self.count)
        self.summary.addWidget(self.average)
        root.addLayout(self.summary)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 14, 14, 14)
        actions = QHBoxLayout()
        actions.addWidget(styled_label("Roster & grade", "cardTitle"))
        actions.addStretch()
        actions.addWidget(button("Record Score", self.record_score, True))
        actions.addWidget(button("Period Setup", self.configure_periods))
        actions.addWidget(button("Save Midterm", self.save_midterm))
        actions.addWidget(button("Save Grades", self.save_period_grades))
        audit = button('Audit history', self.show_audit)
        audit.setVisible(self.app.can('delete'))
        actions.addWidget(audit)
        l.addLayout(actions)
        self.roster = table(["Enrollment", "Student", "Program", "Status", "Final Grade"])
        self.roster.setHorizontalHeaderLabels(['Student Number', 'Student', 'Program', 'Status', 'Overall (%)'])
        self.roster.setProperty('outputTitle', 'Class scores')
        l.addWidget(self.roster)
        root.addWidget(card, 1)
        self.grade_sheet = table(['Student Number', 'Student', 'Midterm', 'Final', 'Overall', 'Readiness'])
        self.grade_sheet.setProperty('outputTitle', 'Period grade sheet')
        sheet_card = Card()
        sheet_layout = QVBoxLayout(sheet_card)
        sheet_layout.setContentsMargins(14, 14, 14, 14)
        sheet_layout.addWidget(styled_label('Grade sheet · saved grade points', 'cardTitle'))
        sheet_layout.addWidget(self.grade_sheet)
        root.addWidget(sheet_card, 1)
        self.refresh_offerings()

    def refresh(self):
        self.refresh_offerings()

    def refresh_offerings(self):
        try:
            selected = self.offering.currentData()
            self.offering.blockSignals(True)
            self.offering.clear()
            for o in self.app.data.offerings():
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]} · {o[5]}", o[0])
            selected_index = self.offering.findData(selected)
            if selected_index >= 0:
                self.offering.setCurrentIndex(selected_index)
            if self.offering.count():
                self.load_class()
            else:
                self.current_offering = None
                fill_table(self.roster, [])
                fill_table(self.grade_sheet, [])
                self.count.setValue(0)
                self.average.setValue("—")
        except Exception as e:
            self.app.error(str(e))
        finally:
            self.offering.blockSignals(False)

    def load_class(self):
        oid = self.offering.currentData()
        if not oid:
            return
        self.current_offering = oid
        try:
            rows = []
            grades = []
            enrollments = self.app.data.enrollments_for_offering(oid)
            for e in enrollments:
                try:
                    g, status = saved_result(self.app.data,e[0])
                    if not g:
                        raise ValueError(status)
                    value = float(g['overall_grade'])
                    text = f"{value:.2f}%"
                    grades.append(value)
                except ValueError as error:
                    text = str(error)
                rows.append((e[1], f"{e[2]} {e[3]}", e[4], e[5], text))
            fill_table(self.roster, rows)
            for row, enrollment in enumerate(enrollments):
                self.roster.item(row, 0).setData(ENROLLMENT_ROLE, enrollment[0])
            self.load_grade_sheet(oid, enrollments)
            self.count.setValue(len(rows))
            self.average.setValue(f"{sum(grades)/len(grades):.1f}%" if grades else "—")
        except Exception as e:
            self.app.error(str(e))

    def load_grade_sheet(self, oid, enrollments):
        apply_report(self.grade_sheet, class_report(self.app.data,oid,grade_sheet=True))

    def show_audit(self):
        if not self.app.can('delete'):
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Grade audit history')
        dialog.resize(1000,540)
        layout = QVBoxLayout(dialog)
        audit_table = table(['When','Who','Table','Record','Action','Before','After'])
        rows = sorted(self.app.data.records()['audit_log'], key=lambda r:r['log_id'],reverse=True)
        fill_table(audit_table,[[str(r.get(k) or '') for k in ['changed_at','changed_by','table_name','record_id','action','old_value','new_value']] for r in rows])
        layout.addWidget(audit_table)
        dialog.exec()

    def configure_periods(self):
        if not self.current_offering:
            return
        dialog = PeriodPolicyDialog(self, self.current_offering, self.app.data.records())
        if dialog.exec() == QDialog.Accepted:
            policy, weights = dialog.values()
            reference=dialog.source.text().strip() or None
            self.app.run_write(lambda: self.app.period_service.save_policy(policy, weights, source_reference=reference), 'Period grading configuration saved.')

    def save_period_grades(self):
        row = self.roster.currentRow()
        if row < 0:
            self.app.warning('Select a student in the roster first.')
            return
        eid = self.roster.item(row, 0).data(ENROLLMENT_ROLE)
        self.app.run_write(lambda: self.app.period_service.calculate_and_save(eid),
                           lambda result: f"Period grades saved. Overall: {result['overall']:.2f}%")

    def save_midterm(self):
        row=self.roster.currentRow()
        if row<0:
            self.app.warning('Select a student in the roster first.')
            return
        eid=self.roster.item(row,0).data(ENROLLMENT_ROLE)
        self.app.run_write(lambda:self.app.period_service.calculate_and_save(eid,period='midterm'),
            lambda result:f"Midterm saved: {result['midterm']:.2f}%")

    def record_score(self):
        row = self.roster.currentRow()
        if row < 0:
            self.app.warning("Select a student first.")
            return
        eid = self.roster.item(row, 0).data(ENROLLMENT_ROLE)
        components = self.app.data.components_for_offering(self.current_offering)
        scores = [s for s in self.app.data.records()['grade_component_score'] if s['enrollment_id']==eid]
        d = ScoreDialog(self, eid, components, scores=scores)
        if d.exec() != QDialog.Accepted:
            return
        try:
            score_id, cid, score, remarks = d.values()
            if d.delete_requested:
                self.app.run_write(lambda: self.app.deletion_service.delete('grade_component_score',score_id),'Score deleted. Re-enter it and recompute to complete the grade.')
                return
            self.app.run_write(lambda: self.app.score_service.record_score(score_id, eid, cid, score, remarks),
                               "Score recorded.")
        except Exception as e:
            self.app.error(str(e))



class RosterPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        actions = QWidget()
        header = QHBoxLayout(actions)
        header.setContentsMargins(0, 0, 0, 0)
        self.teacher = QComboBox()
        self.teacher.currentIndexChanged.connect(self.refresh_offerings)
        header.addWidget(self.teacher)
        self.offering = QComboBox()
        self.offering.currentIndexChanged.connect(self.refresh)
        header.addWidget(self.offering)
        root.addWidget(PageHeader("Class / Section", "A clean roster view for each class offering.", actions))
        hero = Card()
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(22, 18, 22, 18)
        self.class_name = QLabel("Select a class")
        self.class_name.setObjectName("cardTitle")
        hl.addWidget(self.class_name)
        self.class_meta = QLabel("")
        self.class_meta.setObjectName("subtitle")
        self.class_meta.setWordWrap(True)
        hl.addWidget(self.class_meta)
        root.addWidget(hero)
        body = Card()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        self.roster = table(['No.','Student Name','Course'])
        bl.addWidget(self.roster)
        root.addWidget(body, 1)
        self.refresh_offerings()

    def refresh_offerings(self):
        selected = self.offering.currentData()
        selected_teacher = self.teacher.currentData()
        self.teacher.blockSignals(True)
        self.teacher.clear()
        self.teacher.addItem('All teacher',None)
        for teacher in self.app.data.teachers():
            self.teacher.addItem(f'{teacher[1]} {teacher[2]}',teacher[0])
        index=self.teacher.findData(selected_teacher)
        if index>=0:
            self.teacher.setCurrentIndex(index)
        self.teacher.blockSignals(False)
        self.offering.blockSignals(True)
        self.offering.clear()
        try:
            for o in self.app.data.offerings():
                if self.teacher.currentData() is None or o[7] == self.teacher.currentData():
                    self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]}", o[0])
        except Exception as e:
            self.app.error(str(e))
        selected_index = self.offering.findData(selected)
        if selected_index >= 0:
            self.offering.setCurrentIndex(selected_index)
        self.offering.blockSignals(False)
        if self.offering.count():
            self.refresh()
        else:
            fill_table(self.roster, [])
            self.class_name.setText("Select a class")
            self.class_meta.clear()

    def refresh(self):
        oid = self.offering.currentData()
        if not oid:
            return
        try:
            report=class_report(self.app.data,oid)
            self.class_name.setText(report['metadata'][0])
            self.class_meta.setText('\n'.join(report['metadata'][1:]))
            apply_report(self.roster,report)
        except Exception as e:
            self.app.error(str(e))


class ReportsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        actions = QWidget()
        header = QHBoxLayout(actions)
        header.setContentsMargins(0, 0, 0, 0)
        self.student = QComboBox()
        self.student.currentIndexChanged.connect(lambda: self.load_student(self.student.currentData()))
        header.addWidget(self.student)
        self.term = QComboBox()
        self.term.currentIndexChanged.connect(lambda: self.load_student(self.student.currentData()))
        header.addWidget(self.term)
        header.addWidget(button("Refresh", self.app.reload_data, False, True))
        root.addWidget(PageHeader("Student Report", "Saved subject grade and a units-weighted average for the selected term.", actions))
        profile = Card()
        pl = QVBoxLayout(profile)
        pl.setContentsMargins(22, 18, 22, 18)
        self.name = QLabel("Select a student")
        self.name.setObjectName("cardTitle")
        self.info = QLabel("")
        self.info.setObjectName("subtitle")
        self.summary = QLabel("—")
        self.summary.setObjectName("reportSummary")
        self.summary.setWordWrap(True)
        pl.addWidget(self.name)
        pl.addWidget(self.info)
        pl.addWidget(self.summary)
        root.addWidget(profile)
        body = Card()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        self.list = table(['No.','Subject Code','Description','Teacher','Units','F Grade'])
        bl.addWidget(self.list)
        root.addWidget(body, 1)
        self.refresh()

    def refresh(self):
        students = self.app.data.students()
        selected = self.student.currentData()
        self.student.blockSignals(True)
        self.student.clear()
        for s in students:
            self.student.addItem(f"{s[0]} · {s[1]} {s[2]}", s[0])
        selected_index = self.student.findData(selected)
        if selected_index >= 0:
            self.student.setCurrentIndex(selected_index)
        self.student.blockSignals(False)
        self.load_student(self.student.currentData())

    def load_student(self, sid):
        if not sid:
            self.name.setText("Select a student")
            self.info.clear()
            self.summary.setText("No grade available")
            fill_table(self.list, [])
            return
        try:
            terms=sorted({(e[7],e[8]) for e in self.app.data.enrollments_for_student(sid)},reverse=True)
            selected=self.term.currentData()
            self.term.blockSignals(True)
            self.term.clear()
            for term in terms:
                self.term.addItem(f'{term[0]} · {term[1]} Semester',term)
            index=self.term.findData(selected)
            if index>=0:
                self.term.setCurrentIndex(index)
            self.term.blockSignals(False)
            s=self.app.data.student(sid)
            self.name.setText(f'{s[2]}, {s[1]}')
            if not terms:
                self.info.setText(f'{s[0]} · {s[4]}')
                self.summary.setText('No enrollment in this term')
                fill_table(self.list,[])
                self.list.setProperty('reportMetadata',[])
                self.list.setProperty('reportSummary',[])
                return
            report=student_report(self.app.data,sid,*self.term.currentData())
            self.info.setText(f'{s[0]} · {s[4]} · Year {s[6] or "not entered"}')
            self.summary.setText('   ·   '.join(report['summary']))
            apply_report(self.list,report)
        except Exception as e:
            self.app.error(str(e))


class ImportPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.service = SchoolDataImportService()
        self.folder = None
        self.datasets = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(14)
        actions = QWidget()
        header = QHBoxLayout(actions)
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(button("Select Folder", self.select_folder, True))
        root.addWidget(PageHeader("Data Import", "Validate the complete school dataset before touching PostgreSQL.", actions))

        self.path = QLabel("No dataset folder selected")
        self.path.setObjectName("subtitle")
        root.addWidget(self.path)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.addWidget(styled_label(f"{len(DATASETS)} DATASETS", "eyebrow"))
        self.rows = QGridLayout()
        self.rows.setVerticalSpacing(8)
        l.addLayout(self.rows)
        root.addWidget(card)

        bottom = QHBoxLayout()
        self.status = QLabel("Select the test_data folder to begin.")
        self.status.setObjectName("subtitle")
        bottom.addWidget(self.status)
        bottom.addStretch()
        self.validate_btn = button("Validate Data", self.validate)
        self.import_btn = button("Import Entire Dataset", self.import_data, True)
        self.validate_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        bottom.addWidget(self.validate_btn)
        bottom.addWidget(self.import_btn)
        root.addLayout(bottom)
        self.render_rows()

    def render_rows(self):
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.row_labels = {}
        for i, (table_name, filename, _) in enumerate(DATASETS):
            name = QLabel(table_name.replace("_", " ").title())
            name.setObjectName("cardTitle")
            file_label = QLabel(filename)
            file_label.setObjectName("subtitle")
            status = QLabel("NOT SELECTED")
            status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            status.setProperty("badge", "muted")
            self.rows.addWidget(name, i, 0)
            self.rows.addWidget(file_label, i, 1)
            self.rows.addWidget(status, i, 2)
            self.row_labels[table_name] = status

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select school dataset folder")
        if not folder:
            return
        self.folder = folder
        self.datasets = None
        self.path.setText(folder)
        self.validate_btn.setEnabled(True)
        self.import_btn.setEnabled(False)
        for table_name, filename, _ in DATASETS:
            self.row_labels[table_name].setText("FOUND" if os.path.isfile(os.path.join(folder, filename)) else "MISSING")
        self.status.setText("Folder selected. Validate all datasets before importing.")

    def validate(self):
        if not self.folder or getattr(self, "_validating", False):
            return
        self._validating = True
        self.datasets = None
        self.status.setText("Validating all datasets…")
        self.validate_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        folder = self.folder

        def work():
            datasets = self.service.read_folder(folder)
            return datasets, self.service.validate(datasets)

        def done(result):
            self._validating = False
            self.validate_btn.setEnabled(True)
            if folder != self.folder:
                return
            datasets, errors = result
            if errors:
                self.status.setText(f"Validation failed: {len(errors)} issue(s).")
                QMessageBox.warning(self, "Validation failed", "\n".join(errors[:40]))
                return
            self.datasets = datasets
            total = sum(len(datasets.get(name,[])) for name,_,_ in DATASETS)
            for name,_,_ in DATASETS:
                rows=datasets.get(name,[])
                self.row_labels[name].setText(f"{len(rows)} RECORDS")
            self.import_btn.setEnabled(True)
            self.status.setText(f"Validation passed · {total} records ready.")

        def failed(error):
            self._validating = False
            self.validate_btn.setEnabled(True)
            self.status.setText("Validation failed.")
            self.app.error(error)

        self.app.jobs.submit(work, done, failed)

    def import_data(self):
        if not self.datasets or self.app._writing:
            return
        if QMessageBox.question(self, "Import dataset", "Import all datasets in one PostgreSQL transaction?") != QMessageBox.Yes:
            return
        datasets = self.datasets
        total = sum(len(datasets.get(name,[])) for name,_,_ in DATASETS)
        self.import_btn.setEnabled(False)
        self.status.setText("Importing school data…")

        def done(result):
            self.status.setText(f"Import complete · {total} records committed.")

        def failed(error):
            self.status.setText("Import failed. Transaction rolled back.")
            self.import_btn.setEnabled(True)

        self.app.run_write(lambda: self.service.import_all(datasets),
                           f"{total} records were committed successfully.", done, failed)


class StudentHub(BorderlessWindow):
    data_loaded = Signal()

    def __init__(self, session, auth_service=None):
        super().__init__()
        self.session = session
        self.auth = auth_service or AccountService()
        self.account = self.auth.resolve(session)
        self.guard = AccessGuard(self.auth, session)
        self.deletion_service = RecordDeletionService(self.guard)
        self.setWindowTitle("Student Hub · Information & Grading")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)

        self.student_service = SecuredService(StudentService(), self.guard)
        self.academic_service = SecuredService(AcademicService(), self.guard)
        self.period_service = SecuredService(PeriodGradingService(), self.guard)
        self.enrollment_service = SecuredService(EnrollmentService(), self.guard, {'save': ('enrollment', None)})
        self.score_service = SecuredService(ScoreService(), self.guard)

        self.data = DataSnapshot()
        self.jobs = BackgroundJobs(self)
        self._loading = False
        self._reload_again = False
        self._writing = False
        self._closing = False
        self._data_version = 0
        self._rendered_versions = {}
        self.build_ui()
        self.source_reference=QLineEdit()
        self.source_reference.setPlaceholderText("Optional source / reference for changes")
        self.source_reference.setMaximumWidth(320)
        self.title_bar.layout().insertWidget(1,self.source_reference)
        self.apply_permissions()
        QTimer.singleShot(0, self.reload_data)
        self.auto_refresh = QTimer(self)
        self.auto_refresh.setInterval(60000)
        self.auto_refresh.timeout.connect(self.reload_data)
        self.auto_refresh.start()

    def can(self, action):
        return allowed(self.account['role'], action)

    def apply_permissions(self):
        actions = {'Add student': 'student', 'Edit student':'student', 'Delete student':'delete',
                   'Update selected status':'enrollment','Remove selected enrollment':'delete', 'Enroll Student': 'enrollment',
                   'Record Score': 'scores',
                   'Save Grades': 'grade', 'Save Midterm':'grade', 'Period Setup': 'grading'}
        for control in self.findChildren(QPushButton):
            if control.text() in actions:
                control.setEnabled(self.can(actions[control.text()]))
        self.nav_buttons['import'].setVisible(self.can('import'))
        self.import_page.service = SecuredService(self.import_page.service, self.guard, {
            'read_folder': ('import', None), 'validate': ('import', None)})

    def sign_out(self):
        if self._writing:
            self.warning('Wait for the current save before signing out.')
            return
        def done(_):
            self._signed_out = True
            self.close()
        self.jobs.submit(lambda: self.auth.logout(self.session), done, self.error)

    def build_ui(self):
        central = QWidget()
        central.setObjectName("window")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 5, 8, 8)
        outer.setSpacing(0)
        self.title_bar = TitleBar(self)
        outer.addWidget(self.title_bar)
        body = QWidget()
        outer.addWidget(body, 1)
        shell = QHBoxLayout(body)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(8)

        nav = QFrame()
        nav.setObjectName("sidebar")
        self.sidebar = nav
        self.sidebar_labels = []
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 14, 12, 12)
        nl.setSpacing(4)

        brand = QLabel("S")
        brand.setObjectName("brandMark")
        brand.setText("SH")
        nl.addWidget(brand)
        brand_title = QLabel("Student Hub")
        brand_title.setObjectName("brandTitle")
        nl.addWidget(brand_title)
        self.sidebar_labels.append(brand_title)
        self.sidebar_toggle = QToolButton()
        self.sidebar_toggle.setObjectName('sidebarToggle')
        self.sidebar_toggle.setIcon(sidebar_icon('panel-left.svg', MUTED))
        self.sidebar_toggle.setIconSize(QSize(20, 20))
        self.sidebar_toggle.setFixedHeight(36)
        self.sidebar_toggle.clicked.connect(
            lambda: self.set_sidebar_expanded(not self.sidebar_expanded))
        nl.addSpacing(12)
        nl.addWidget(self.sidebar_toggle)
        nl.addSpacing(10)
        section_label = styled_label("WORKSPACE", "eyebrow")
        self.sidebar_labels.append(section_label)
        nl.addWidget(section_label)

        self.nav_buttons = {}
        items = [
            ("dashboard", "Dashboard", "house.svg"),
            ("grade", "Class Grades", "chart.svg"),
            ("reports", "Reports", "file-text.svg"),
            ("academic", "Academic", "book-open.svg"),
            ("enrollment", "Enrollments", "users-round.svg"),
            ("roster", "Class / Section", "graduation-cap.svg"),
            ("import", "Data Import", "upload.svg"),
        ]
        if self.can('accounts'):
            items.extend([('accounts', 'Accounts', 'users-round.svg'), ('records', 'Data Records', 'file-text.svg')])
        for key, text, icon_name in items:
            if key in ("academic", "import"):
                nl.addSpacing(10)
                section_label = styled_label("SCHOOL RECORDS" if key == "academic" else "ADMINISTRATION", "eyebrow")
                self.sidebar_labels.append(section_label)
                nl.addWidget(section_label)
            b = QToolButton()
            b.setText(text)
            b.setToolTip(text)
            b.setAccessibleName(text)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(40)
            b.setIcon(sidebar_icon(icon_name, MUTED))
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setIconSize(QSize(21, 21))
            b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setProperty("icon_name", icon_name)
            b.normal_icon = sidebar_icon(icon_name, MUTED)
            b.active_icon = sidebar_icon(icon_name, ON_ACCENT)
            b.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            nl.addWidget(b)
            self.nav_buttons[key] = b
        nl.addStretch()

        identity = QFrame()
        identity.setObjectName("sidebarIdentity")
        il = QVBoxLayout(identity)
        il.setContentsMargins(0, 10, 0, 4)
        il.setSpacing(5)
        self.account_initials = ''.join(part[0] for part in self.account['full_name'].split()[:2]).upper() or 'SH'
        avatar = QLabel(self.account_initials)
        avatar.setObjectName('accountAvatar')
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setToolTip(f"{self.account['full_name']} · {ROLES[self.account['role']]}")
        il.addWidget(avatar, 0, Qt.AlignHCenter)
        workspace_label = styled_label("YOUR WORKSPACE", "identityEyebrow")
        self.sidebar_labels.append(workspace_label)
        il.addWidget(workspace_label)
        identity_title = QLabel(self.account['full_name'])
        identity_title.setObjectName("identityTitle")
        identity_title.setWordWrap(True)
        il.addWidget(identity_title)
        identity_meta = QLabel(ROLES[self.account['role']])
        identity_meta.setObjectName("identityMeta")
        il.addWidget(identity_meta)
        self.sidebar_labels.extend([identity_title, identity_meta])
        nl.addWidget(identity)
        self.sign_out_button = QToolButton()
        self.sign_out_button.setText('Sign out')
        self.sign_out_button.setToolTip('Sign out')
        self.sign_out_button.setAccessibleName('Sign out')
        self.sign_out_button.setIcon(sidebar_icon('log-out.svg', MUTED))
        self.sign_out_button.setFixedHeight(40)
        self.sign_out_button.clicked.connect(self.sign_out)
        nl.addWidget(self.sign_out_button)

        nl.addSpacing(10)


        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName('sidebarScroll')
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        self.sidebar_scroll = sidebar_scroll
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setWidget(nav)
        shell.addWidget(sidebar_scroll)
        self.set_sidebar_expanded(False)

        content = QFrame()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(24, 0, 24, 0)
        tl.addWidget(styled_label("SCHOOL MANAGEMENT", "topbarContext"))
        tl.addStretch()
        current_date = QLabel(date.today().strftime("%A, %d %B %Y"))
        current_date.setObjectName("topbarDate")
        current_date.setVisible(False)
        tl.addWidget(current_date)
        self.output_table = QComboBox()
        self.output_table.setMinimumWidth(140)
        self.output_table.setMaximumWidth(210)
        tl.addWidget(self.output_table)
        tl.addWidget(button("Export CSV", self.export_current, compact=True))
        tl.addWidget(button("Print", self.print_current, compact=True))
        tl.addWidget(button("Refresh", self.reload_data, compact=True))
        profile = QLabel(self.account_initials)
        profile.setObjectName('accountAvatar')
        profile.setFixedSize(32, 32)
        profile.setAlignment(Qt.AlignCenter)
        profile.setToolTip(f"{self.account['full_name']} · {ROLES[self.account['role']]}")
        tl.addSpacing(6)
        tl.addWidget(profile)
        cl.addWidget(topbar)
        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.page_motion = PageReveal(self.stack)
        cl.addWidget(self.stack, 1)
        shell.addWidget(content, 1)

        self.pages = {}
        self.dashboard = DashboardPage(self)
        self.grades = GradesPage(self)
        self.reports = ReportsPage(self)
        self.academic = AcademicPage(self)
        self.enrollments = EnrollmentsPage(self)
        self.roster = RosterPage(self)
        self.import_page = ImportPage(self)
        for key, page in [
            ("dashboard", self.dashboard), ("grade", self.grades), ("reports", self.reports),
            ("academic", self.academic), ("enrollment", self.enrollments),
            ("roster", self.roster), ("import", self.import_page)
        ] + ([('accounts', AccountsPage(self, table, fill_table)), ('records', DataRecordsPage(self, table, fill_table))] if self.can('accounts') else []):
            page.setObjectName("workspacePage")
            names = {"student_table": "Students", "teacher_table": "Teachers",
                     "subject_table": "Subjects", "period_table": "Grading periods",
                     "offering_table": "Class offerings", "roster": "Class roster",
                     "list": "Student report" if key == "reports" else "Enrollments"}
            for attribute, name in names.items():
                widget = getattr(page, attribute, None)
                if isinstance(widget, QTableWidget) and not widget.property('outputTitle'):
                    widget.setProperty("outputTitle", name)
            for combo in page.findChildren(QComboBox):
                combo.setMinimumContentsLength(12)
                combo.setMaximumWidth(340)
                combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            self.pages[key] = page
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)
        # Sidebar controls share the same feedback as page actions.
        for control in self.findChildren(QToolButton):
            control.motion_feedback = InteractionFeedback(control)
        self.show_page("dashboard")

    def set_sidebar_expanded(self, expanded):
        """Keep the same controls, focus and permissions when toggling labels."""
        self.sidebar_expanded = expanded
        width = 224 if expanded else 80
        self.sidebar.setFixedWidth(width)
        self.sidebar_scroll.setFixedWidth(width)
        style = Qt.ToolButtonTextBesideIcon if expanded else Qt.ToolButtonIconOnly
        for control in [*self.nav_buttons.values(), self.sign_out_button]:
            control.setToolButtonStyle(style)
        for label in self.sidebar_labels:
            label.setVisible(expanded)
        action = 'Collapse navigation' if expanded else 'Expand navigation'
        self.sidebar_toggle.setToolTip(action)
        self.sidebar_toggle.setAccessibleName(action)

    def show_page(self, key):
        if key == 'import' and not self.can('import'):
            self.warning('Only an Admin can import school data.')
            return
        changed = getattr(self, "current_page", None) != key
        self.page_motion.cancel()
        self.stack.setCurrentIndex(list(self.pages).index(key))
        self.current_page = key
        self.update_output_tables()
        for k, b in self.nav_buttons.items():
            active = k == key
            b.setChecked(active)
            b.setIcon(b.active_icon if active else b.normal_icon)
        self.render_page(key)

        if changed:
            self.page_motion.reveal()

    def update_output_tables(self):
        self.output_table.clear()
        page = self.pages[self.current_page]
        for widget in page.findChildren(QTableWidget):
            name = widget.property("outputTitle") or "Records"
            self.output_table.addItem(name, widget)
        enabled = self.output_table.count() > 0
        self.output_table.setEnabled(enabled)

    def export_current(self):
        widget = self.output_table.currentData()
        if widget is not None:
            export_table(self, widget, self.output_table.currentText())
        else:
            self.warning("This page has no table to export.")

    def print_current(self):
        widget = self.output_table.currentData()
        if widget is not None:
            print_table(self, widget, self.output_table.currentText())
        else:
            self.warning("This page has no table to print.")

    def render_page(self, key):
        if self._rendered_versions.get(key) == self._data_version:
            return
        page = self.pages[key]
        try:
            if key == "roster":
                page.refresh_offerings()
            else:
                refresh = getattr(page, "refresh", None)
                if callable(refresh):
                    refresh()
            self._rendered_versions[key] = self._data_version
        except Exception as error:
            self.error(str(error))

    def reload_data(self):
        if self._closing:
            return
        if self._writing:
            self._reload_again = True
            return
        if self._loading:
            self._reload_again = True
            return
        self._loading = True
        self.title_bar.status.setText("Updating school data…")
        def read():
            try:
                account = self.auth.resolve(self.session)
            except PermissionError as error:
                raise PermissionError('Signed out: ' + str(error)) from error
            return scope_snapshot(load_snapshot(), account)
        self.jobs.submit(read, self.accept_snapshot, self.load_failed)

    def accept_snapshot(self, snapshot):
        self._loading = False
        if self._reload_again:
            self._reload_again = False
            self.reload_data()
            return
        self.page_motion.cancel()
        self.data = snapshot
        self._data_version += 1
        self.render_page(self.current_page)
        self.title_bar.status.setText("School data up to date" if not self._writing else "Saving…")
        self.data_loaded.emit()

    def load_failed(self, message):
        self._loading = False
        self._reload_again = False
        self.title_bar.status.setText("Could not update school data")
        if message.startswith('Signed out:'):
            self.data = DataSnapshot()
            self.stack.setEnabled(False)
            self.stack.hide()
        self.error(message)

    def run_write(self, operation, message, after=None, on_failure=None):
        if self._writing:
            self.warning("A save is still in progress. Please wait a moment.")
            return
        self._writing = True
        self.title_bar.status.setText("Saving…")

        def done(result):
            self._writing = False
            self._reload_again = False
            self.reload_data()
            if after:
                after(result)
            self.success(message(result) if callable(message) else message)

        def failed(error):
            self._writing = False
            self.title_bar.status.setText("Save failed")
            if on_failure:
                on_failure(error)
            self.error(error)

        from app.database.provenance import write_source
        reference=self.source_reference.text().strip()
        def work():
            with write_source(reference):
                return operation()
        self.jobs.submit(work, done, failed)

    def refresh_all(self):
        self.reload_data()

    def enrollment_repo_count(self):
        return self.data.enrollment_count

    def closeEvent(self, event):
        self._closing = True
        self.auto_refresh.stop()
        self.jobs.detach()
        super().closeEvent(event)

    def error(self, message):
        QMessageBox.critical(self, "Something went wrong", message)

    def warning(self, message):
        QMessageBox.warning(self, "Attention", message)

    def success(self, message):
        QMessageBox.information(self, "Saved", message)



def run():
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    auth = AccountService()
    while True:
        login = LoginDialog(auth)
        if login.exec() != QDialog.Accepted:
            return 0
        try:
            window = StudentHub(login.token, auth)
        except Exception as error:
            QMessageBox.critical(None, 'Unable to open Student Hub', str(error))
            return 1
        window.show()
        result = app.exec()
        if not getattr(window, '_signed_out', False):
            return result
