from datetime import date
import os
import sys

from PySide6.QtCore import Qt, QSize, QByteArray
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QToolButton, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog,
    QScrollArea, QTabWidget, QAbstractItemView, QSizePolicy
)

from app.gui.table_output import export_table, print_table
from app.gui.motion import InteractionFeedback, PageReveal

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


BG = "#F5F7FA"
SURFACE = "#FFFFFF"
SURFACE_2 = "#F8FAFC"
SURFACE_3 = "#EEF2F7"
TEXT = "#172033"
MUTED = "#64748B"
PURPLE = "#3158D4"
PURPLE_HOVER = "#2448BB"
PURPLE_SOFT = "#E9EEFF"
MINT = "#DCF4EA"
MINT_TEXT = "#16785A"
BLUE = "#E5EFFF"
BLUE_TEXT = "#3158D4"
PEACH = "#FFF0E8"
PEACH_TEXT = "#B45309"
YELLOW = "#FFF7D6"
YELLOW_TEXT = "#9A6700"
BORDER = "#E2E8F0"
DANGER = "#C2414B"


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
        self.setStyleSheet(f"QFrame#statCard {{ background: {accent}; border: 0; }} "
                           "QFrame#statCard QLabel { color: white; background: transparent; }")
        title.setObjectName("eyebrow")
        dot = QLabel()
        icon_name = {"Students": "users-round.svg", "Enrollments": "file-text.svg",
                     "Teachers": "graduation-cap.svg", "Class Offerings": "book-open.svg"}.get(label, "chart.svg")
        dot.setPixmap(sidebar_icon(icon_name, "#FFFFFF", 28).pixmap(28, 28))
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
    for row in range(t.rowCount()):
        t.setRowHeight(row, 44)


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
        for control in buttons.buttons():
            control.motion_feedback = InteractionFeedback(control)
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
        for control in buttons.buttons():
            control.motion_feedback = InteractionFeedback(control)
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

        root.addWidget(PageHeader("Dashboard", "School activity and student performance at a glance.",
                                  button("Add student", self.add_student, True)))

        overview = QFrame()
        overview.setObjectName("dashboardOverview")
        ol = QHBoxLayout(overview)
        ol.setContentsMargins(24, 18, 24, 18)
        copy = QVBoxLayout()
        copy.setSpacing(4)
        kicker = QLabel("ACADEMIC OVERVIEW")
        kicker.setObjectName("overviewKicker")
        copy.addWidget(kicker)
        headline = QLabel("A focused view of school activity and student progress.")
        headline.setObjectName("overviewTitle")
        headline.setWordWrap(True)
        copy.addWidget(headline)
        self.overview_detail = QLabel("Loading current records from PostgreSQL.")
        self.overview_detail.setObjectName("overviewDetail")
        copy.addWidget(self.overview_detail)
        ol.addLayout(copy, 1)
        overview_action = button("Review class grades", lambda: self.app.show_page("grades"), True)
        ol.addWidget(overview_action, 0, Qt.AlignVCenter)
        root.addWidget(overview)

        stats = QGridLayout()
        stats.setSpacing(14)
        self.students_stat = StatCard("Students", "0", PURPLE)
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
        refresh = button("↻", self.refresh, False, True)
        refresh.setFixedWidth(42)
        sh.addWidget(refresh)
        sl.addLayout(sh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, ID, program…")
        self.search.textChanged.connect(self.filter_students)
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
            self._students = students
            self.filter_students()
            self.students_stat.setValue(len(students))
            self.enrollments_stat.setValue(self.app.enrollment_repo_count())
            self.teachers_stat.setValue(len(self.app.teacher_repo.find_all()))
            offerings = self.app.offering_repo.find_all()
            self.classes_stat.setValue(len(offerings))
            self.overview_detail.setText(
                f"{len(students)} students across {len(offerings)} class offering(s)."
            )
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
            self.student_table.selectRow(0)
        else:
            self.selected_student = None
            self.selected_name.setText("No student selected")
            self.selected_info.setText("Add a student or adjust your search.")
            self.grade_label.setText("—")
            self.enrollment_label.setText("No enrollments selected")

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
        index = self.app.reports.student.findData(self.selected_student)
        self.app.reports.student.setCurrentIndex(index)
        self.app.reports.load_student(self.selected_student)


class AcademicPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 26)
        root.setSpacing(18)
        root.addWidget(PageHeader("Academic", "Teachers, subjects, grading periods and class offerings.", button("Refresh", self.refresh)))
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tab_motion = PageReveal(self.tabs)
        self.tabs.currentChanged.connect(lambda: self.tab_motion.reveal())
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
        root.addWidget(PageHeader("Enrollments", "Connect students to class offerings without leaving the workspace.", button("Refresh", self.refresh)))

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
        form.addWidget(styled_label("ENROLLMENT ID", "eyebrow"), 2, 0)
        form.addWidget(styled_label("STATUS", "eyebrow"), 2, 1)
        self.enrollment_id = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["Active", "Dropped", "Completed"])
        form.addWidget(self.enrollment_id, 3, 0)
        form.addWidget(self.status, 3, 1)
        save = button("Enroll Student", self.save, True)
        form.addWidget(save, 4, 1, Qt.AlignRight)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)
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

    def refresh(self):
        self.refresh_offerings()

    def refresh_offerings(self):
        try:
            self.offering.blockSignals(True)
            self.offering.clear()
            for o in self.app.offering_repo.find_all():
                self.offering.addItem(f"{o[11]} · {o[12]} · {o[3]} · {o[5]}", o[0])
            if self.offering.count():
                self.load_class()
            else:
                self.current_offering = None
                fill_table(self.roster, [])
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
        self.load_student(self.student.currentData())

    def load_student(self, sid):
        if not sid:
            self.name.setText("Select a student")
            self.info.clear()
            self.summary.setText("No grades available")
            fill_table(self.list, [])
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



class StudentHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Hub · Information & Grading")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)

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
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("sidebar")
        nav.setFixedWidth(210)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(18, 22, 18, 18)
        nl.setSpacing(6)

        brand = QLabel("S")
        brand.setObjectName("brandMark")
        brand.setText("SH")
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
            if key in ("academic", "import"):
                nl.addSpacing(14)
                nl.addWidget(styled_label("ACADEMIC RECORDS" if key == "academic" else "DATA TOOLS", "eyebrow"))
            b = QToolButton()
            b.setText(text)
            b.setIcon(sidebar_icon(icon_name, MUTED))
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setIconSize(QSize(21, 21))
            b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        identity_title = QLabel("School workspace")
        identity_title.setObjectName("identityTitle")
        identity_title.setWordWrap(True)
        il.addWidget(identity_title)
        identity_meta = QLabel("Students · Classes · Grades")
        identity_meta.setObjectName("identityMeta")
        il.addWidget(identity_meta)
        nl.addWidget(identity)

        nl.addSpacing(10)


        shell.addWidget(nav)

        content = QFrame()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(30, 0, 32, 0)
        tl.addWidget(styled_label("SCHOOL MANAGEMENT", "topbarContext"))
        tl.addStretch()
        current_date = QLabel(date.today().strftime("%A, %d %B %Y"))
        current_date.setObjectName("topbarDate")
        current_date.setVisible(False)
        tl.addWidget(current_date)
        self.output_table = QComboBox()
        self.output_table.setMinimumWidth(140)
        tl.addWidget(self.output_table)
        tl.addWidget(button("Export CSV", self.export_current, compact=True))
        tl.addWidget(button("Print", self.print_current, compact=True))
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
            ("dashboard", self.dashboard), ("grades", self.grades), ("reports", self.reports),
            ("academic", self.academic), ("enrollments", self.enrollments),
            ("roster", self.roster), ("import", self.import_page)
        ]:
            page.setObjectName("workspacePage")
            names = {"student_table": "Students", "teacher_table": "Teachers",
                     "subject_table": "Subjects", "period_table": "Grading periods",
                     "offering_table": "Class offerings", "roster": "Class roster",
                     "list": "Student report" if key == "reports" else "Enrollments"}
            for attribute, name in names.items():
                widget = getattr(page, attribute, None)
                if isinstance(widget, QTableWidget):
                    widget.setProperty("outputTitle", name)
            for combo in page.findChildren(QComboBox):
                combo.setMinimumContentsLength(12)
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

    def show_page(self, key):
        changed = getattr(self, "current_page", None) != key
        self.page_motion.cancel()
        self.stack.setCurrentIndex(list(self.pages).index(key))
        self.current_page = key
        self.update_output_tables()
        for k, b in self.nav_buttons.items():
            active = k == key
            b.setChecked(active)
            icon_name = b.property("icon_name")
            b.setIcon(sidebar_icon(icon_name, PURPLE if active else MUTED))
        page = self.pages[key]
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as e:
                self.error(str(e))

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

    def refresh_all(self):
        for page in self.pages.values():
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                try:
                    refresh()
                except Exception as error:
                    self.error(str(error))

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
QWidget {{ color: {TEXT}; font-family: "Segoe UI"; font-size: 13px; }}
QWidget#window, QWidget#workspacePage, QStackedWidget, QScrollArea {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QFrame#sidebar {{ background: white; border: 0; border-radius: 0; }}
QFrame#content {{ background: {BG}; border: 0; }}
QFrame#topbar {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; min-height: 64px; max-height: 64px; }}
QLabel#topbarContext, QLabel#brandMeta {{ color: #93A4C3; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#topbarContext {{ color: {MUTED}; }}
QLabel#topbarDate {{ color: {MUTED}; font-size: 12px; }}
QLabel#brandMark {{ background: {PURPLE}; color: white; border-radius: 10px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; font-size: 12px; font-weight: 800; qproperty-alignment: AlignCenter; }}
QLabel#brandTitle {{ color: {TEXT}; font-size: 16px; font-weight: 750; padding: 0; }}
QLabel#pageTitle {{ color: {TEXT}; font-size: 27px; font-weight: 750; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 13px; }}
QLabel#eyebrow {{ color: {MUTED}; font-size: 10px; font-weight: 750; letter-spacing: 1px; padding: 0; }}
QLabel#cardTitle, QLabel#sectionTitle {{ color: {TEXT}; font-size: 16px; font-weight: 750; }}
QLabel#statValue {{ color: {TEXT}; font-size: 28px; font-weight: 750; }}
QLabel#heroGrade {{ color: {PURPLE}; font-size: 30px; font-weight: 800; padding-top: 4px; }}
QLabel#sidebarFoot {{ color: #7182A2; font-size: 10px; }}
QFrame#sidebarIdentity {{ background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 10px; }}
QLabel#identityEyebrow {{ color: #93A4C3; font-size: 9px; font-weight: 800; letter-spacing: 1px; }}
QLabel#identityTitle {{ color: {TEXT}; font-size: 13px; font-weight: 700; }}
QLabel#identityMeta {{ color: {MUTED}; font-size: 10px; }}
QFrame#card, QFrame#sectionCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#statCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; min-height: 112px; }}
QFrame#dashboardOverview {{ background: #1C3D90; border: 0; border-radius: 12px; }}
QLabel#overviewKicker {{ color: #BFD0FF; font-size: 10px; font-weight: 800; letter-spacing: 1px; }}
QLabel#overviewTitle {{ color: white; font-size: 21px; font-weight: 700; }}
QLabel#overviewDetail {{ color: #DCE6FF; font-size: 12px; }}
QToolButton {{ background: transparent; color: {MUTED}; border: 0; border-radius: 8px; text-align: left; padding: 10px 11px; font-size: 13px; font-weight: 600; spacing: 10px; }}
QToolButton:hover {{ background: {SURFACE_3}; color: {TEXT}; }}
QToolButton:checked {{ background: {PURPLE_SOFT}; color: {PURPLE}; }}
QPushButton {{ background: {SURFACE_3}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 13px; min-height: 18px; font-weight: 650; }}
QPushButton:hover {{ background: #E1E9FA; border-color: #C7D3EE; }}
QPushButton[primary="true"] {{ background: {PURPLE}; color: white; border-color: {PURPLE}; }}
QPushButton[primary="true"]:hover {{ background: {PURPLE_HOVER}; }}
QPushButton[compact="true"] {{ padding: 6px 9px; }}
QLineEdit, QComboBox, QDateEdit {{ background: {SURFACE}; color: {TEXT}; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 10px; min-height: 18px; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {PURPLE}; background: white; }}
QTableWidget {{ background: {SURFACE}; border: 0; border-radius: 8px; alternate-background-color: #F8FAFC; selection-background-color: {PURPLE_SOFT}; selection-color: {TEXT}; gridline-color: transparent; outline: 0; }}
QHeaderView::section {{ background: #F8FAFC; color: {MUTED}; border: 0; border-bottom: 1px solid {BORDER}; padding: 11px 10px; font-size: 10px; font-weight: 800; }}
QTableWidget::item {{ padding: 10px; border-bottom: 1px solid #EEF2F6; }}
QTableWidget::item:hover {{ background: #F5F8FF; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; background: {SURFACE}; top: -1px; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; border: 0; border-bottom: 2px solid transparent; border-radius: 0; padding: 10px 14px; margin-right: 5px; font-weight: 700; }}
QTabBar::tab:selected {{ color: {PURPLE}; border-bottom-color: {PURPLE}; background: transparent; }}
QDialog {{ background: {SURFACE}; }}
QScrollBar:vertical {{ background: {SURFACE_3}; width: 10px; border: 0; }}
QScrollBar::handle:vertical {{ background: #B8C5D6; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QDialogButtonBox QPushButton {{ min-width: 88px; }}
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
