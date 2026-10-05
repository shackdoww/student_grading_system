from datetime import date
import os
import sys

from PySide6.QtCore import Qt, QSize, QDate, QByteArray
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QToolButton, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QScrollArea, QDateEdit, QTabWidget, QAbstractItemView, QProgressBar
)

from app.repositories.class_offering_repository import ClassOfferingRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.grade_percentage_repository import GradePercentageRepository
from app.repositories.grading_period_repository import GradingPeriodRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.school_data_import_service import SchoolDataImportService, DATASETS
from app.services.score_service import ScoreService
from app.services.student_service import StudentService


BG = "#F7F5FC"
SURFACE = "#FFFFFF"
SURFACE_2 = "#F1EDFA"
SURFACE_3 = "#EAE4F7"
TEXT = "#29263A"
MUTED = "#827B96"
PURPLE = "#7657E8"
PURPLE_HOVER = "#6849D5"
PURPLE_SOFT = "#E7E0FF"
MINT = "#DDF7EC"
MINT_TEXT = "#27845D"
BLUE = "#DDEEFF"
BLUE_TEXT = "#3977A9"
PEACH = "#FFE5DE"
PEACH_TEXT = "#B95F4D"
YELLOW = "#FFF1C9"
YELLOW_TEXT = "#9A721A"
BORDER = "#E4DEEF"
DANGER = "#D85C67"


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
        title = QLabel(label.upper())
        title.setObjectName("eyebrow")
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{accent};font-size:11px;")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(dot)
        layout.addLayout(top)
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        layout.addWidget(self.value)

    def setValue(self, value):
        self.value.setText(str(value))


def table(columns, rows=0):
    t = QTableWidget(rows, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.setAlternatingRowColors(False)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setSectionResizeMode(len(columns) - 1, QHeaderView.Stretch)
    t.setShowGrid(False)
    return t


def fill_table(t, rows):
    t.setRowCount(len(rows))
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            item = QTableWidgetItem("" if value is None else str(value))
            item.setData(Qt.UserRole, value)
            t.setItem(r, c, item)
    t.resizeRowsToContents()


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
            ("Program", "program"), ("Status", "status")
        ]
        for label, key in labels:
            w = QLineEdit()
            self.fields[key] = w
            form.addRow(label, w)
        if student:
            for i, key in enumerate(self.fields):
                self.fields[key].setText(str(student[i]))
        else:
            self.fields["status"].setText("Active")
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return {key: w.text().strip() for key, w in self.fields.items()}


class ScoreDialog(QDialog):
    def __init__(self, parent, enrollment_id, components):
        super().__init__(parent)
        self.setWindowTitle("Record Score")
        self.setMinimumWidth(460)
        form = QFormLayout(self)
        form.setContentsMargins(26, 24, 26, 18)
        self.score_id = QLineEdit(f"SC-{enrollment_id}-")
        self.component = QComboBox()
        for row in components:
            self.component.addItem(f"{row[1]}  ·  max {float(row[3]):g}", row[0])
        self.score = QLineEdit()
        self.remarks = QLineEdit()
        form.addRow("Score ID", self.score_id)
        form.addRow("Component", self.component)
        form.addRow("Score", self.score)
        form.addRow("Remarks", self.remarks)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return self.score_id.text().strip(), self.component.currentData(), self.score.text().strip(), self.remarks.text().strip()


class DashboardPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.selected_student = None
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)

        header = QHBoxLayout()
        title = QVBoxLayout()
        h = QLabel("Good day")
        h.setObjectName("pageTitle")
        sub = QLabel("A calm overview of your school data and student performance.")
        sub.setObjectName("subtitle")
        title.addWidget(h)
        title.addWidget(sub)
        header.addLayout(title)
        header.addStretch()
        header.addWidget(button("＋  Add Student", self.add_student, True))
        root.addLayout(header)

        stats = QGridLayout()
        stats.setSpacing(14)
        self.students_stat = StatCard("Students", "0", PURPLE)
        self.enrollments_stat = StatCard("Enrollments", "0", "#5B9EE8")
        self.teachers_stat = StatCard("Teachers", "0", "#55BE8C")
        self.classes_stat = StatCard("Class Offerings", "0", "#F2B94B")
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
        refresh = button("↻", self.refresh, False, True)
        refresh.setFixedWidth(42)
        sh.addWidget(refresh)
        sl.addLayout(sh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, ID, program…")
        self.search.textChanged.connect(self.refresh)
        sl.addWidget(self.search)
        self.student_table = table(["ID", "Name", "Program", "Status"])
        self.student_table.itemSelectionChanged.connect(self.student_selected)
        sl.addWidget(self.student_table)
        workspace.addWidget(students_card, 3)

        side = QVBoxLayout()
        side.setSpacing(16)
        selected = Card()
        il = QVBoxLayout(selected)
        il.setContentsMargins(20, 20, 20, 20)
        il.addWidget(styled_label("SELECTED STUDENT", "eyebrow"))
        self.selected_name = QLabel("Select a student")
        self.selected_name.setObjectName("cardTitle")
        il.addWidget(self.selected_name)
        self.selected_info = QLabel("Choose a student from the list to view their academic snapshot.")
        self.selected_info.setObjectName("subtitle")
        self.selected_info.setWordWrap(True)
        il.addWidget(self.selected_info)
        self.grade_label = QLabel("—")
        self.grade_label.setObjectName("heroGrade")
        il.addWidget(self.grade_label)
        self.enrollment_label = QLabel("No enrollment selected")
        self.enrollment_label.setObjectName("subtitle")
        il.addWidget(self.enrollment_label)
        il.addStretch()
        side.addWidget(selected, 2)

        quick = Card()
        ql = QVBoxLayout(quick)
        ql.setContentsMargins(20, 18, 20, 18)
        ql.addWidget(styled_label("QUICK ACTIONS", "eyebrow"))
        ql.addWidget(button("View Class Grades", lambda: self.app.show_page("grades")))
        ql.addWidget(button("Open Academic", lambda: self.app.show_page("academic")))
        ql.addWidget(button("Manage Enrollments", lambda: self.app.show_page("enrollments")))
        ql.addWidget(button("Student Report", self.open_report))
        side.addWidget(quick, 1)
        workspace.addLayout(side, 2)
        root.addLayout(workspace, 1)

    def refresh(self):
        try:
            students = self.app.student_service.get_all()
            q = self.search.text().lower().strip()
            filtered = [s for s in students if not q or q in " ".join(map(str, s)).lower()]
            fill_table(self.student_table, [(s[0], f"{s[1]} {s[2]}", s[4], s[5]) for s in filtered])
            self.students_stat.setValue(len(students))
            self.enrollments_stat.setValue(self.app.enrollment_repo_count())
            self.teachers_stat.setValue(len(self.app.teacher_repo.find_all()))
            self.classes_stat.setValue(len(self.app.offering_repo.find_all()))
            if self.student_table.rowCount() and not self.student_table.selectedItems():
                self.student_table.selectRow(0)
        except Exception as e:
            self.app.error(str(e))

    def student_selected(self):
        rows = self.student_table.selectedItems()
        if not rows:
            return
        sid = self.student_table.item(self.student_table.currentRow(), 0).text()
        try:
            student = self.app.student_service.get(sid)
            self.selected_student = sid
            self.selected_name.setText(f"{student[1]} {student[2]}")
            self.selected_info.setText(f"{student[0]}  ·  {student[4]}  ·  {student[3]}  ·  {student[5]}")
            enrollments = self.app.enrollment_service.get_by_student(sid)
            self.enrollment_label.setText(f"{len(enrollments)} enrollment(s)")
            grades = []
            for e in enrollments:
                try:
                    g = self.app.grading_service.get_saved_grade(e[0])
                    grades.append(float(g[1]) if g else float(self.app.grading_service.calculate_grade(e[0])))
                except Exception:
                    pass
            self.grade_label.setText(f"{sum(grades)/len(grades):.1f}%" if grades else "—")
        except Exception as e:
            self.app.error(str(e))

    def add_student(self):
        d = StudentDialog(self)
        if d.exec() != QDialog.Accepted:
            return
        try:
            v = d.values()
            self.app.student_service.save(**v)
            self.refresh()
        except Exception as e:
            self.app.error(str(e))

    def open_report(self):
        if not self.selected_student:
            self.app.warning("Select a student first.")
            return
        self.app.show_page("reports")
        self.app.reports.load_student(self.selected_student)


class AcademicPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Academic", "pageTitle"))
        box.addWidget(styled_label("Teachers, subjects, grading periods and class offerings.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        header.addWidget(button("↻ Refresh", self.refresh))
        root.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs, 1)

        self.teacher_table = table(["ID", "Name", "Email", "Department", "Status"])
        self.subject_table = table(["ID", "Code", "Subject", "Units", "Description"])
        self.period_table = table(["ID", "Name", "Start", "End", "School Year", "Semester"])
        self.offering_table = table(["ID", "Class", "Subject", "Section", "Schedule", "Teacher", "Room"])
        for name, t in [("Teachers", self.teacher_table), ("Subjects", self.subject_table),
                        ("Grading Periods", self.period_table), ("Class Offerings", self.offering_table)]:
            card = Card()
            l = QVBoxLayout(card)
            l.setContentsMargins(14, 14, 14, 14)
            l.addWidget(t)
            self.tabs.addTab(card, name)

    def refresh(self):
        try:
            teachers = self.app.teacher_repo.find_all()
            fill_table(self.teacher_table, [(r[0], f"{r[1]} {r[2]}", r[3], r[4], r[5]) for r in teachers])
            subjects = self.app.subject_repo.find_all()
            fill_table(self.subject_table, [(r[0], r[1], r[2], r[4], r[3] or "—") for r in subjects])
            periods = self.app.period_repo.find_all()
            fill_table(self.period_table, [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in periods])
            offerings = self.app.offering_repo.find_all()
            fill_table(self.offering_table, [(r[0], r[1], r[11] + " — " + r[12], r[3], r[2], f"{r[8]} {r[9]}", r[6] or "—") for r in offerings])
        except Exception as e:
            self.app.error(str(e))


class EnrollmentsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Enrollments", "pageTitle"))
        box.addWidget(styled_label("Connect students to class offerings without leaving the workspace.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        header.addWidget(button("↻ Refresh", self.refresh))
        root.addLayout(header)

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
        form.addWidget(styled_label("ENROLLMENT ID", "eyebrow"), 0, 2)
        form.addWidget(styled_label("STATUS", "eyebrow"), 0, 3)
        self.enrollment_id = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["Active", "Dropped", "Completed"])
        form.addWidget(self.enrollment_id, 1, 2)
        form.addWidget(self.status, 1, 3)
        save = button("Enroll Student", self.save, True)
        form.addWidget(save, 1, 4)
        root.addWidget(editor)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 14, 14, 14)
        l.addWidget(styled_label("Current enrollment roster", "cardTitle"))
        self.list = table(["Enrollment", "Student", "Class", "Section", "Program", "Status"])
        l.addWidget(self.list)
        root.addWidget(card, 1)
        self.refresh()

    def refresh(self):
        try:
            students = self.app.student_service.get_all()
            offerings = self.app.offering_repo.find_all()
            self.student.clear()
            for s in students:
                self.student.addItem(f"{s[0]} · {s[1]} {s[2]}", s[0])
            self.offering.clear()
            for o in offerings:
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]}", o[0])
            if not self.enrollment_id.text():
                self.enrollment_id.setText(f"E-{len(self.app.enrollment_repo.find_by_student_id(students[0][0])) + 1}" if students else "E-001")
            rows = []
            for o in offerings:
                for e in self.app.enrollment_repo.find_by_offering_id(o[0]):
                    rows.append((e[0], f"{e[2]} {e[3]}", o[1], o[3], e[4], e[5]))
            fill_table(self.list, rows)
        except Exception as e:
            self.app.error(str(e))

    def save(self):
        if not self.student.currentData() or not self.offering.currentData():
            return
        try:
            self.app.enrollment_service.save(self.enrollment_id.text().strip(), date.today(), self.status.currentText(),
                                             self.student.currentData(), self.offering.currentData())
            self.refresh()
            self.app.success("Enrollment saved.")
        except Exception as e:
            self.app.error(str(e))


class GradesPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.current_offering = None
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Class Grades", "pageTitle"))
        box.addWidget(styled_label("Select a class, inspect its roster, and record scores.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        self.offering = QComboBox()
        self.offering.currentIndexChanged.connect(self.load_class)
        header.addWidget(self.offering)
        root.addLayout(header)

        self.summary = QHBoxLayout()
        self.count = StatCard("Students", "0", PURPLE)
        self.average = StatCard("Class Average", "—", "#55BE8C")
        self.summary.addWidget(self.count)
        self.summary.addWidget(self.average)
        root.addLayout(self.summary)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 14, 14, 14)
        actions = QHBoxLayout()
        actions.addWidget(styled_label("Roster & grades", "cardTitle"))
        actions.addStretch()
        actions.addWidget(button("Record Score", self.record_score, True))
        actions.addWidget(button("Save Grade", self.save_grade))
        l.addLayout(actions)
        self.roster = table(["Enrollment", "Student", "Program", "Status", "Final Grade"])
        l.addWidget(self.roster)
        root.addWidget(card, 1)
        self.refresh_offerings()

    def refresh_offerings(self):
        try:
            self.offering.blockSignals(True)
            self.offering.clear()
            for o in self.app.offering_repo.find_all():
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]} · {o[5]}", o[0])
            self.offering.blockSignals(False)
            if self.offering.count():
                self.load_class()
        except Exception as e:
            self.app.error(str(e))

    def load_class(self):
        oid = self.offering.currentData()
        if not oid:
            return
        self.current_offering = oid
        try:
            rows = []
            grades = []
            enrollments = self.app.enrollment_service.get_by_offering(oid)
            for e in enrollments:
                try:
                    g = self.app.grading_service.get_saved_grade(e[0])
                    value = float(g[1]) if g else float(self.app.grading_service.calculate_grade(e[0]))
                    text = f"{value:.2f}%"
                    grades.append(value)
                except Exception:
                    text = "No grade yet"
                rows.append((e[0], f"{e[2]} {e[3]}", e[4], e[5], text))
            fill_table(self.roster, rows)
            self.count.setValue(len(rows))
            self.average.setValue(f"{sum(grades)/len(grades):.1f}%" if grades else "—")
        except Exception as e:
            self.app.error(str(e))

    def record_score(self):
        row = self.roster.currentRow()
        if row < 0:
            self.app.warning("Select a student first.")
            return
        eid = self.roster.item(row, 0).text()
        components = self.app.component_repo.find_by_offering_id(self.current_offering)
        d = ScoreDialog(self, eid, components)
        if d.exec() != QDialog.Accepted:
            return
        try:
            score_id, cid, score, remarks = d.values()
            self.app.score_service.record_score(score_id, eid, cid, score, remarks)
            self.load_class()
            self.app.success("Score recorded.")
        except Exception as e:
            self.app.error(str(e))

    def save_grade(self):
        row = self.roster.currentRow()
        if row < 0:
            self.app.warning("Select a student first.")
            return
        eid = self.roster.item(row, 0).text()
        try:
            grade = self.app.grading_service.calculate_and_save_grade(eid)
            self.load_class()
            self.app.success(f"Grade saved: {grade:.2f}%")
        except Exception as e:
            self.app.error(str(e))


class RosterPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Class / Section", "pageTitle"))
        box.addWidget(styled_label("A clean roster view for each class offering.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        self.offering = QComboBox()
        self.offering.currentIndexChanged.connect(self.refresh)
        header.addWidget(self.offering)
        root.addLayout(header)
        hero = Card()
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(22, 18, 22, 18)
        self.class_name = QLabel("Select a class")
        self.class_name.setObjectName("cardTitle")
        hl.addWidget(self.class_name)
        self.class_meta = QLabel("")
        self.class_meta.setObjectName("subtitle")
        hl.addWidget(self.class_meta)
        root.addWidget(hero)
        body = Card()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        self.roster = table(["Enrollment", "Student ID", "Name", "Program", "Status"])
        bl.addWidget(self.roster)
        root.addWidget(body, 1)
        self.refresh_offerings()

    def refresh_offerings(self):
        self.offering.blockSignals(True)
        self.offering.clear()
        try:
            for o in self.app.offering_repo.find_all():
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]}", o[0])
        except Exception as e:
            self.app.error(str(e))
        self.offering.blockSignals(False)
        if self.offering.count():
            self.refresh()

    def refresh(self):
        oid = self.offering.currentData()
        if not oid:
            return
        try:
            offering = next((o for o in self.app.offering_repo.find_all() if o[0] == oid), None)
            if offering:
                self.class_name.setText(f"{offering[11]} · {offering[12]}")
                self.class_meta.setText(f"{offering[1]}  ·  Section {offering[3]}  ·  {offering[2]}  ·  {offering[6] or 'Room TBA'}")
            rows = self.app.enrollment_service.get_by_offering(oid)
            fill_table(self.roster, [(r[0], r[1], f"{r[2]} {r[3]}", r[4], r[5]) for r in rows])
        except Exception as e:
            self.app.error(str(e))


class ReportsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Student Report", "pageTitle"))
        box.addWidget(styled_label("Academic snapshot with calculated or saved grades.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        self.student = QComboBox()
        self.student.currentIndexChanged.connect(lambda: self.load_student(self.student.currentData()))
        header.addWidget(self.student)
        header.addWidget(button("↻", lambda: self.load_student(self.student.currentData()), False, True))
        root.addLayout(header)
        profile = Card()
        pl = QVBoxLayout(profile)
        pl.setContentsMargins(22, 18, 22, 18)
        self.name = QLabel("Select a student")
        self.name.setObjectName("cardTitle")
        self.info = QLabel("")
        self.info.setObjectName("subtitle")
        self.summary = QLabel("—")
        self.summary.setObjectName("heroGrade")
        pl.addWidget(self.name)
        pl.addWidget(self.info)
        pl.addWidget(self.summary)
        root.addWidget(profile)
        body = Card()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        self.list = table(["Enrollment", "Subject", "Class", "Section", "Semester", "Status", "Final Grade"])
        bl.addWidget(self.list)
        root.addWidget(body, 1)
        self.refresh()

    def refresh(self):
        students = self.app.student_service.get_all()
        self.student.blockSignals(True)
        self.student.clear()
        for s in students:
            self.student.addItem(f"{s[0]} · {s[1]} {s[2]}", s[0])
        self.student.blockSignals(False)
        if self.student.count():
            self.load_student(self.student.currentData())

    def load_student(self, sid):
        if not sid:
            return
        try:
            s = self.app.student_service.get(sid)
            self.name.setText(f"{s[1]} {s[2]}")
            self.info.setText(f"{s[0]}  ·  {s[4]}  ·  {s[3]}  ·  {s[5]}")
            rows = []
            grades = []
            for e in self.app.enrollment_service.get_by_student(sid):
                try:
                    g = self.app.grading_service.get_saved_grade(e[0])
                    value = float(g[1]) if g else float(self.app.grading_service.calculate_grade(e[0]))
                    grade_text = f"{value:.2f}%"
                    grades.append(value)
                except Exception:
                    grade_text = "No grade yet"
                rows.append((e[0], f"{e[11]} — {e[12]}", e[4], e[6], e[8], e[2], grade_text))
            fill_table(self.list, rows)
            self.summary.setText(f"Average {sum(grades)/len(grades):.2f}%" if grades else "No grades available")
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
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        header = QHBoxLayout()
        box = QVBoxLayout()
        box.addWidget(styled_label("Data Import", "pageTitle"))
        box.addWidget(styled_label("Validate the complete school dataset before touching PostgreSQL.", "subtitle"))
        header.addLayout(box)
        header.addStretch()
        header.addWidget(button("Select Folder", self.select_folder, True))
        root.addLayout(header)

        self.path = QLabel("No dataset folder selected")
        self.path.setObjectName("subtitle")
        root.addWidget(self.path)

        card = Card()
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.addWidget(styled_label("10 DATASETS", "eyebrow"))
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
        try:
            self.status.setText("Validating all 10 datasets…")
            QApplication.processEvents()
            datasets = self.service.read_folder(self.folder)
            errors = self.service.validate(datasets)
            if errors:
                self.import_btn.setEnabled(False)
                QMessageBox.warning(self, "Validation failed", "\n".join(f"• {e}" for e in errors[:40]))
                self.status.setText(f"Validation failed: {len(errors)} issue(s).")
                return
            self.datasets = datasets
            total = sum(len(v) for v in datasets.values())
            for name, rows in datasets.items():
                self.row_labels[name].setText(f"{len(rows)} RECORDS")
            self.import_btn.setEnabled(True)
            self.status.setText(f"Validation passed · {total} records ready.")
        except Exception as e:
            self.app.error(str(e))

    def import_data(self):
        if not self.datasets:
            return
        if QMessageBox.question(self, "Import dataset", "Import all 10 datasets in one PostgreSQL transaction?") != QMessageBox.Yes:
            return
        try:
            total = sum(len(v) for v in self.datasets.values())
            self.service.import_all(self.datasets)
            self.app.refresh_all()
            self.status.setText(f"Import complete · {total} records committed.")
            self.import_btn.setEnabled(False)
            QMessageBox.information(self, "Import complete", f"{total} records were committed successfully.")
        except Exception as e:
            self.app.error(f"Import failed. Transaction rolled back.\n\n{e}")



class PatternBackground(QWidget):
    """Soft decorative background that adds depth without competing with the data."""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BG))

        for x, y, size, color, alpha in [
            (-90, -70, 260, PURPLE, 24),
            (self.width() - 180, 35, 220, "#7BC7B1", 20),
            (self.width() - 120, self.height() - 170, 250, "#F0B45B", 18),
        ]:
            c = QColor(color)
            c.setAlpha(alpha)
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y, size, size)

        dot = QColor(PURPLE)
        dot.setAlpha(42)
        painter.setBrush(dot)
        painter.setPen(Qt.NoPen)
        for row in range(5):
            for col in range(7):
                painter.drawEllipse(28 + col * 13, 30 + row * 13, 3, 3)

        pen = QPen(QColor(PURPLE))
        pen.setAlpha(35)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(self.width() - 210, self.height() - 130, 180, 110, 20 * 16, 120 * 16)
        painter.end()


class StudentHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Hub · Information & Grading")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()
        self.teacher_repo = TeacherRepository()
        self.subject_repo = SubjectRepository()
        self.period_repo = GradingPeriodRepository()
        self.offering_repo = ClassOfferingRepository()
        self.enrollment_repo = EnrollmentRepository()
        self.component_repo = GradeComponentRepository()
        self.percentage_repo = GradePercentageRepository()

        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        central = QWidget()
        central.setObjectName("window")
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(14, 14, 14, 14)
        shell.setSpacing(14)

        nav = QFrame()
        nav.setObjectName("sidebar")
        nav.setFixedWidth(224)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(14, 18, 14, 16)
        nl.setSpacing(6)

        brand = QLabel("S")
        brand.setObjectName("brandMark")
        nl.addWidget(brand)
        brand_title = QLabel("STUDENT HUB")
        brand_title.setObjectName("brandTitle")
        nl.addWidget(brand_title)
        nl.addSpacing(18)
        nl.addWidget(styled_label("MAIN MENU", "eyebrow"))

        self.nav_buttons = {}
        items = [
            ("dashboard", "Dashboard", "house.svg"),
            ("grades", "Class Grades", "chart.svg"),
            ("reports", "Reports", "file-text.svg"),
            ("academic", "Academic", "book-open.svg"),
            ("enrollments", "Enrollments", "users-round.svg"),
            ("roster", "Class / Section", "graduation-cap.svg"),
            ("import", "Data Import", "upload.svg"),
        ]
        for key, text, icon_name in items:
            b = QToolButton()
            b.setText(text)
            b.setIcon(sidebar_icon(icon_name, MUTED))
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setIconSize(QSize(21, 21))
            b.setCheckable(True)
            b.setProperty("icon_name", icon_name)
            b.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            nl.addWidget(b)
            self.nav_buttons[key] = b
        nl.addStretch()

        identity = QFrame()
        identity.setObjectName("sidebarIdentity")
        il = QVBoxLayout(identity)
        il.setContentsMargins(14, 12, 14, 12)
        il.setSpacing(5)
        il.addWidget(styled_label("YOUR WORKSPACE", "identityEyebrow"))
        identity_title = QLabel("Everything in one place")
        identity_title.setObjectName("identityTitle")
        identity_title.setWordWrap(True)
        il.addWidget(identity_title)
        identity_meta = QLabel("Students · Classes · Grades")
        identity_meta.setObjectName("identityMeta")
        il.addWidget(identity_meta)
        nl.addWidget(identity)

        nl.addSpacing(10)
        nl.addWidget(styled_label("POSTGRESQL SCHOOL SYSTEM", "sidebarFoot"))
        nl.addWidget(styled_label("Desktop workspace · PySide6", "sidebarFoot"))
        shell.addWidget(nav)

        content = QFrame()
        content.setObjectName("content")
        cl = QGridLayout(content)
        cl.setContentsMargins(4, 2, 4, 2)
        self.pattern = PatternBackground()
        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.stack.setAttribute(Qt.WA_TranslucentBackground)
        cl.addWidget(self.pattern, 0, 0)
        cl.addWidget(self.stack, 0, 0)
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
            ("dashboard", self.dashboard), ("grades", self.grades), ("reports", self.reports),
            ("academic", self.academic), ("enrollments", self.enrollments),
            ("roster", self.roster), ("import", self.import_page)
        ]:
            page.setAttribute(Qt.WA_TranslucentBackground)
            self.pages[key] = page
            self.stack.addWidget(page)
        self.show_page("dashboard")

    def show_page(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        for k, b in self.nav_buttons.items():
            active = k == key
            b.setChecked(active)
            icon_name = b.property("icon_name")
            b.setIcon(sidebar_icon(icon_name, "#FFFFFF" if active else MUTED))
        page = self.pages[key]
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as e:
                self.error(str(e))

    def refresh_all(self):
        for page in self.pages.values():
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                try:
                    refresh()
                except Exception:
                    pass

    def enrollment_repo_count(self):
        try:
            # Count through offerings to avoid adding a new repository just for the dashboard.
            return sum(len(self.enrollment_repo.find_by_offering_id(o[0])) for o in self.offering_repo.find_all())
        except Exception:
            return 0

    def error(self, message):
        QMessageBox.critical(self, "Something went wrong", message)

    def warning(self, message):
        QMessageBox.warning(self, "Attention", message)

    def success(self, message):
        QMessageBox.information(self, "Saved", message)


STYLE = f"""
QWidget#window, QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 13px;
}}
QFrame#sidebar {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 24px;
}}
QFrame#content {{
    background: transparent;
}}
QStackedWidget#pageStack {{
    background: transparent;
    border: 0;
}}
QLabel#brandMark {{
    background: {PURPLE_SOFT};
    color: {PURPLE};
    border-radius: 20px;
    min-width: 46px;
    max-width: 46px;
    min-height: 46px;
    max-height: 46px;
    padding: 0;
    font-size: 24px;
    font-weight: 800;
    qproperty-alignment: AlignCenter;
}}
QLabel#brandTitle {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 800;
    padding-left: 2px;
}}
QLabel#pageTitle {{
    color: {TEXT};
    font-size: 30px;
    font-weight: 800;
}}
QLabel#subtitle {{
    color: {MUTED};
    font-size: 13px;
}}
QLabel#eyebrow {{
    color: {MUTED};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QLabel#cardTitle {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 750;
}}
QLabel#statValue {{
    color: {TEXT};
    font-size: 28px;
    font-weight: 800;
}}
QLabel#heroGrade {{
    color: {PURPLE};
    font-size: 30px;
    font-weight: 850;
    padding-top: 6px;
}}
QLabel#sidebarFoot {{
    color: {MUTED};
    font-size: 10px;
}}
QFrame#sidebarIdentity {{
    background: {PURPLE_SOFT};
    border: 1px solid #DDD3FF;
    border-radius: 18px;
}}
QLabel#identityEyebrow {{
    color: {PURPLE};
    font-size: 9px;
    font-weight: 850;
    letter-spacing: 1px;
}}
QLabel#identityTitle {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 800;
}}
QLabel#identityMeta {{
    color: {MUTED};
    font-size: 10px;
}}
QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 22px;
}}
QFrame#card[accent="mint"] {{
    background: {MINT};
    border-color: {MINT};
}}
QToolButton {{
    background: transparent;
    color: {MUTED};
    border: 0;
    border-radius: 14px;
    text-align: left;
    padding: 11px 13px;
    font-size: 13px;
    font-weight: 650;
    spacing: 10px;
}}
QToolButton:hover {{
    background: {SURFACE_2};
    color: {TEXT};
}}
QToolButton:checked {{
    background: {PURPLE};
    color: white;
    padding-left: 14px;
}}
QPushButton {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 0;
    border-radius: 12px;
    padding: 10px 16px;
    min-height: 18px;
    font-weight: 700;
}}
QPushButton:hover {{
    background: {SURFACE_3};
}}
QPushButton[primary="true"] {{
    background: {PURPLE};
    color: white;
}}
QPushButton[primary="true"]:hover {{
    background: {PURPLE_HOVER};
}}
QPushButton[compact="true"] {{
    padding: 6px 10px;
}}
QLineEdit, QComboBox, QDateEdit {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 9px 11px;
    min-height: 18px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid {PURPLE};
    background: white;
}}
QTableWidget {{
    background: {SURFACE};
    border: 0;
    border-radius: 14px;
    alternate-background-color: {BG};
    selection-background-color: {PURPLE_SOFT};
    selection-color: {TEXT};
    gridline-color: transparent;
    outline: 0;
}}
QHeaderView::section {{
    background: {SURFACE_2};
    color: {MUTED};
    border: 0;
    padding: 10px 8px;
    font-size: 10px;
    font-weight: 800;
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {BORDER};
}}
QTabWidget::pane {{
    border: 0;
    background: transparent;
}}
QTabBar::tab {{
    background: {SURFACE_2};
    color: {MUTED};
    border: 0;
    border-radius: 11px;
    padding: 10px 16px;
    margin-right: 5px;
    font-weight: 700;
}}
QTabBar::tab:selected {{
    background: {PURPLE};
    color: white;
}}
QMessageBox, QDialog {{
    background: {SURFACE};
}}
"""

def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = StudentHub()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
