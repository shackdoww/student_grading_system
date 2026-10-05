import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv

import customtkinter as ctk

from app.gui.academic_window import AcademicWindow
from app.gui.data_import_window import DataImportWindow
from app.gui.class_grade_window import ClassGradeWindow
from app.gui.class_roster_window import ClassRosterWindow
from app.gui.enrollment_window import EnrollmentWindow
from app.gui.student_report_window import StudentReportWindow
from app.repositories.grade_component_repository import GradeComponentRepository
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService


BG = "#F6F4FB"
SIDEBAR = "#FFFFFF"
PANEL = "#FFFFFF"
PANEL_2 = "#F0ECF8"
BORDER = "#E4DEEF"
ACCENT = "#7C5CFC"
HOVER = "#967CFF"
TEXT = "#28243A"
MUTED = "#827B96"
SUCCESS = "#5BCB9A"
SKY = "#63B3ED"
PEACH = "#FF9F8F"
YELLOW = "#F6C85F"


class StudentGradingGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Student Information and Grading System")
        self.geometry("1240x780")
        self.minsize(1050, 680)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()
        self.component_repository = GradeComponentRepository()
        self.enrollments = []
        self.current_enrollment_id = None

        self._style_tables()
        self._build_ui()
        self.refresh_students()

    def _style_tables(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 24, "bold"))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("TButton", background=PANEL, foreground=TEXT, borderwidth=0,
                        padding=(14, 9), font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", "#E7E1F4")], foreground=[("active", TEXT)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_2, foreground=MUTED,
                        padding=(16, 9), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#FFFFFF")])
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, borderwidth=0, padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, borderwidth=0, rowheight=44,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=PANEL_2,
                        foreground=MUTED, borderwidth=0,
                        font=("Segoe UI", 8, "bold"), padding=(10, 10))
        style.map("Treeview", background=[("selected", "#E5DEFF")],
                  foreground=[("selected", TEXT)])

    def _panel(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER,
                            border_width=1, corner_radius=20, **kw)

    def _nav(self, parent, text, command, active=False):
        return ctk.CTkButton(
            parent, text=text, command=command, anchor="w", height=38,
            corner_radius=16, fg_color=ACCENT if active else "transparent",
            hover_color=HOVER if active else PANEL_2, text_color="#FFFFFF" if active else TEXT,
            font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        shell = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        shell.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(shell, width=215, fg_color=SIDEBAR, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="S", text_color=ACCENT,
                     font=("Segoe UI", 32, "bold")).pack(anchor="w", padx=22, pady=(24, 0))
        ctk.CTkLabel(sidebar, text="STUDENT HUB", text_color=TEXT,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(0, 30))
        ctk.CTkLabel(sidebar, text="MAIN MENU", text_color="#5F6D78",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(0, 8))

        self.nav_buttons = {}
        for key, text in [
            ("dashboard", "▣   Dashboard"),
            ("class_grades", "▤   Class Grades"),
            ("reports", "▥   Reports"),
            ("academic", "⚙   Academic"),
            ("enrollments", "▦   Enrollments"),
            ("class_roster", "▧   Class / Section"),
            ("data_import", "⇩   Data Import"),
        ]:
            button = self._nav(
                sidebar, text, lambda key=key: self.show_card(key),
                active=(key == "dashboard")
            )
            button.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[key] = button

        ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(sidebar, text="SYSTEM", text_color="#5F6D78",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(0, 8))
        self._nav(sidebar, "⟳   Refresh Data", self.refresh_students).pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(sidebar, text="Student Information\nand Grading System",
                     text_color="#596772", justify="left",
                     font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=22, pady=20)

        content = ctk.CTkFrame(shell, fg_color=BG, corner_radius=0)
        content.pack(side="left", fill="both", expand=True)

        self.card_container = ctk.CTkFrame(content, fg_color=BG, corner_radius=0)
        self.card_container.pack(fill="both", expand=True)

        dashboard = ctk.CTkFrame(self.card_container, fg_color=BG, corner_radius=0)
        dashboard.pack(fill="both", expand=True)

        header = ctk.CTkFrame(dashboard, fg_color="transparent", height=66)
        header.pack(fill="x", padx=28, pady=(20, 6))
        header.pack_propagate(False)
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Dashboard", text_color=TEXT,
                     font=("Segoe UI", 27, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="STUDENT OVERVIEW", text_color=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ctk.CTkButton(header, text="⟳", command=self.refresh_students,
                      width=42, height=38, corner_radius=16, fg_color=PANEL_2,
                      hover_color=ACCENT, text_color=ACCENT,
                      font=("Segoe UI", 16, "bold")).pack(side="right", pady=6)

        cards = ctk.CTkFrame(dashboard, fg_color="transparent")
        cards.pack(fill="x", padx=28, pady=(0, 16))
        self.student_count_var = tk.StringVar(value="0")
        self.enrollment_count_var = tk.StringVar(value="0")
        self.final_grade_card_var = tk.StringVar(value="--")
        self.status_card_var = tk.StringVar(value="--")

        for title, var, accent in [
            ("Students", self.student_count_var, False),
            ("Enrollments", self.enrollment_count_var, False),
            ("Current Grade", self.final_grade_card_var, True),
            ("Status", self.status_card_var, False),
        ]:
            box = self._panel(cards, height=88)
            box.pack(side="left", fill="x", expand=True, padx=(0, 10))
            box.pack_propagate(False)
            ctk.CTkLabel(box, text=title.upper(), text_color=MUTED,
                         font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15, pady=(12, 0))
            ctk.CTkLabel(box, textvariable=var,
                         text_color=ACCENT if accent else TEXT,
                         font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=15)

        workspace = ctk.CTkFrame(dashboard, fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        left = self._panel(workspace, width=360)
        left.pack(side="left", fill="both", padx=(0, 12))
        left.pack_propagate(False)
        ctk.CTkLabel(left, text="STUDENTS", text_color=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(14, 7))

        self.student_tree = ttk.Treeview(left, columns=("id", "name", "program", "status"),
                                         show="headings", selectmode="browse")
        for col, title, width in [("id", "ID", 58), ("name", "Name", 125),
                                  ("program", "Program", 78), ("status", "Status", 68)]:
            self.student_tree.heading(col, text=title)
            self.student_tree.column(col, width=width, anchor="w", stretch=col != "id")
        self.student_tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)
        self.student_tree.bind("<Double-1>", self.on_student_selected)

        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(0, 12))
        for text, command in [("ADD", self.add_student), ("EDIT", self.edit_student),
                             ("DELETE", self.delete_student)]:
            ctk.CTkButton(actions, text=text, command=command, height=34,
                          corner_radius=14, fg_color=PANEL_2, hover_color="#30404C",
                          font=("Segoe UI", 8, "bold")).pack(side="left", fill="x",
                                                            expand=True, padx=2)

        right = self._panel(workspace)
        right.pack(side="left", fill="both", expand=True)

        info = ctk.CTkFrame(right, fg_color="transparent")
        info.pack(fill="x", padx=18, pady=(14, 7))
        ctk.CTkLabel(info, text="SELECTED STUDENT", text_color=ACCENT,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.info_var = tk.StringVar(value="Select a student.")
        ctk.CTkLabel(info, textvariable=self.info_var, text_color="#DCE2E6",
                     justify="left", anchor="w", font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        enrollment = ctk.CTkFrame(right, fg_color="transparent")
        enrollment.pack(fill="x", padx=18, pady=(5, 9))
        self.enrollment_combo = ctk.CTkComboBox(
            enrollment, state="readonly", height=36, corner_radius=14,
            fg_color=PANEL_2, border_color=BORDER, button_color=PANEL_2,
            button_hover_color=ACCENT, dropdown_fg_color=PANEL_2,
            dropdown_hover_color="#30404C")
        self.enrollment_combo.pack(side="left", fill="x", expand=True)
        self.enrollment_combo.configure(command=self.on_enrollment_selected)
        ctk.CTkButton(enrollment, text="↻", command=self.refresh_enrollments,
                      width=42, height=36, corner_radius=8, fg_color=PANEL_2,
                      hover_color=ACCENT, text_color=ACCENT,
                      font=("Segoe UI", 14, "bold")).pack(side="left", padx=(7, 0))

        grade = ctk.CTkFrame(right, fg_color="transparent")
        grade.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        top = ctk.CTkFrame(grade, fg_color="transparent", height=30)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="GRADE BREAKDOWN", text_color=ACCENT,
                     font=("Segoe UI", 8, "bold")).pack(side="left")
        self.final_grade_var = tk.StringVar(value="Final Grade: --")
        self.weight_var = tk.StringVar(value="Total Weight: --")
        ctk.CTkLabel(top, textvariable=self.final_grade_var, text_color=TEXT,
                     font=("Segoe UI", 11, "bold")).pack(side="right")
        ctk.CTkLabel(top, textvariable=self.weight_var, text_color=MUTED,
                     font=("Segoe UI", 8)).pack(side="right", padx=12)

        table = ctk.CTkFrame(grade, fg_color=PANEL_2, corner_radius=8)
        table.pack(fill="both", expand=True)
        self.grade_tree = ttk.Treeview(
            table, columns=("category", "component", "score", "percentage", "weight", "weighted"),
            show="headings", height=6)
        for col, title, width in [("category", "Cat.", 50), ("component", "Component", 125),
                                  ("score", "Score", 95), ("percentage", "%", 65),
                                  ("weight", "Weight", 70), ("weighted", "Weighted", 80)]:
            self.grade_tree.heading(col, text=title)
            self.grade_tree.column(col, width=width, anchor="w")
        self.grade_tree.pack(fill="both", expand=True, padx=2, pady=2)

        bottom = ctk.CTkFrame(right, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(0, 13))
        for text, command, color in [
            ("RECORD SCORE", self.open_score_dialog, PANEL_2),
            ("SAVE GRADE", self.calculate_grade, ACCENT),
            ("CLASS GRADES", self.open_class_grades, ACCENT),
            ("STUDENT REPORT", self.open_student_report, PANEL_2),
            ("CLASS / SECTION", self.open_class_roster, PANEL_2)]:
            ctk.CTkButton(bottom, text=text, command=command, height=35,
                          corner_radius=7, fg_color=color,
                          hover_color=HOVER if color == ACCENT else "#E1DAEF",
                          text_color="#FFFFFF" if color == ACCENT else TEXT,
                          font=("Segoe UI", 8, "bold")).pack(side="left", fill="x",
                                                             expand=True, padx=3)

        # Card-based navigation: all major sections stay in this window.
        self.cards = {
            "dashboard": dashboard,
            "class_grades": ClassGradeWindow(self.card_container),
            "academic": AcademicWindow(self.card_container),
            "enrollments": EnrollmentWindow(self.card_container),
            "class_roster": ClassRosterWindow(self.card_container),
            "data_import": DataImportWindow(self.card_container, self),
        }
        self.report_card = None
        for card in self.cards.values():
            card.place_forget()
        self.show_card("dashboard")

    def focus_students(self):
        items = self.student_tree.get_children()
        if items:
            item = self.student_tree.selection()[0] if self.student_tree.selection() else items[0]
            self.student_tree.selection_set(item)
            self.student_tree.focus(item)
            self.student_tree.see(item)
            self.on_student_selected()

    def show_card(self, name):
        if name == "reports":
            sid = self._get_selected_student_id()
            if not sid:
                return
            if self.report_card is not None:
                self.report_card.destroy()
            self.report_card = StudentReportWindow(self.card_container, sid)
            self.cards["reports"] = self.report_card

        for card in self.cards.values():
            card.place_forget()

        card = self.cards.get(name)
        if card is None:
            return
        card.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._set_active_nav(name)

        if name == "enrollments":
            card.refresh()
        elif name == "class_grades":
            card.refresh_offerings()
        elif name == "class_roster":
            card.refresh_offerings()
        elif name == "academic":
            for method in ("refresh_teachers", "refresh_subjects", "refresh_offerings",
                           "refresh_periods", "refresh_percentages", "refresh_components"):
                getattr(card, method)()

    def _set_active_nav(self, name):
        """Highlight only the sidebar button for the currently visible card."""
        for key, button in self.nav_buttons.items():
            active = key == name
            button.configure(
                fg_color=ACCENT if active else "transparent",
                hover_color=HOVER if active else PANEL,
                text_color=BG if active else TEXT,
            )

    def open_academic_management(self):
        self.show_card("academic")

    def open_enrollment_management(self):
        self.show_card("enrollments")

    def open_class_grades(self):
        self.show_card("class_grades")

    def open_class_roster(self):
        self.show_card("class_roster")

    def open_student_report(self):
        self.show_card("reports")

    def refresh_students(self):
        try:
            students = self.student_service.get_all()
            self.student_tree.delete(*self.student_tree.get_children())
            self.student_count_var.set(str(len(students)))
            for s in students:
                self.student_tree.insert("", "end", values=(s[0], f"{s[1]} {s[2]}", s[4], s[5]))
            if students:
                first = self.student_tree.get_children()[0]
                self.student_tree.selection_set(first)
                self.student_tree.focus(first)
                self.on_student_selected()
            else:
                self.info_var.set("No students found.")
                self.enrollment_combo.set("")
                self.clear_grade_view()
        except Exception as e: messagebox.showerror("Database Error", str(e), parent=self)

    def _get_selected_student_id(self):
        selected = self.student_tree.selection()
        if not selected:
            messagebox.showwarning("No Student Selected", "Select a student first.", parent=self)
            return None
        return self.student_tree.item(selected[0], "values")[0]

    def import_students_csv(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Import Student CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        required = ["student_id", "first_name", "last_name", "email", "program", "status"]
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValueError("The CSV file is empty or has no header row.")

                headers = [header.strip() for header in reader.fieldnames]
                missing = [field for field in required if field not in headers]
                if missing:
                    raise ValueError(
                        "Missing required column(s): " + ", ".join(missing) +
                        "\n\nRequired columns:\n" + ", ".join(required)
                    )

                students = []
                for row in reader:
                    students.append({
                        field: (row.get(field) or "").strip()
                        for field in required
                    })

            if not students:
                raise ValueError("The CSV contains a header but no student records.")

            errors = self.student_service.validate_import(students)
            self._show_import_preview(path, students, errors)
        except UnicodeDecodeError:
            messagebox.showerror(
                "CSV Encoding Error",
                "The CSV could not be read as UTF-8. Save the file as UTF-8 CSV and try again.",
                parent=self
            )
        except csv.Error as e:
            messagebox.showerror("CSV Format Error", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)

    def _show_import_preview(self, path, students, errors):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Import Students - Preview")
        dialog.geometry("940x590")
        dialog.minsize(820, 500)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="IMPORT STUDENTS", text_color=ACCENT,
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(
            dialog, text=f"File: {path}",
            text_color=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=24, pady=(0, 10))

        summary = (
            f"{len(students)} student record(s) found. "
            + ("Fix the errors below before importing." if errors
               else "Review the records, then confirm the import.")
        )
        summary_var = tk.StringVar(value=summary)
        ctk.CTkLabel(
            dialog, textvariable=summary_var, text_color=TEXT,
            font=("Segoe UI", 10), justify="left"
        ).pack(anchor="w", padx=24, pady=(0, 8))

        table_frame = ctk.CTkFrame(dialog, fg_color=PANEL_2, corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        columns = ("student_id", "first_name", "last_name", "email", "program", "status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "student_id": ("Student ID", 90),
            "first_name": ("First Name", 105),
            "last_name": ("Last Name", 105),
            "email": ("Email", 210),
            "program": ("Program", 110),
            "status": ("Status", 90),
        }
        for col in columns:
            title, width = headings[col]
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=2, pady=2)

        for student in students:
            tree.insert("", "end", values=tuple(student[col] for col in columns))

        error_frame = ctk.CTkFrame(dialog, fg_color=PANEL, corner_radius=8)
        error_frame.pack(fill="x", padx=24, pady=(0, 10))

        error_text = tk.Text(
            error_frame, height=5, bg=PANEL, fg=TEXT,
            insertbackground=TEXT, relief="flat", borderwidth=0,
            font=("Segoe UI", 9), wrap="word"
        )
        error_text.pack(fill="both", expand=True, padx=10, pady=8)

        if errors:
            error_text.insert("1.0", "IMPORT BLOCKED:\n" + "\n".join("• " + e for e in errors))
        else:
            existing_ids = {
                row[0] for row in self.student_service.get_all()
            }
            updates = sum(1 for student in students if student["student_id"] in existing_ids)
            new_count = len(students) - updates
            error_text.insert(
                "1.0",
                f"Ready to import: {new_count} new student(s), {updates} existing "
                "student ID(s) will be updated."
            )
        error_text.configure(state="disabled")

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(0, 18))

        import_button = ctk.CTkButton(
            buttons, text="IMPORT STUDENTS", height=38, corner_radius=8,
            fg_color=ACCENT, hover_color=HOVER, text_color=BG,
            font=("Segoe UI", 9, "bold")
        )
        import_button.pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            buttons, text="CANCEL", command=dialog.destroy, height=38,
            corner_radius=8, fg_color=PANEL_2, hover_color=BORDER,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        if errors:
            import_button.configure(state="disabled")
        else:
            def confirm_import():
                try:
                    self.student_service.import_students(students)
                    dialog.destroy()
                    self.refresh_students()
                    messagebox.showinfo(
                        "Import Complete",
                        f"Successfully imported {len(students)} student record(s).\n"
                        "Existing Student IDs were updated.",
                        parent=self
                    )
                except Exception as e:
                    messagebox.showerror("Import Failed", str(e), parent=dialog)

            import_button.configure(command=confirm_import)

    def add_student(self): self.open_student_dialog()

    def edit_student(self):
        sid = self._get_selected_student_id()
        if sid:
            try: self.open_student_dialog(self.student_service.get(sid))
            except Exception as e: messagebox.showerror("Student Error", str(e), parent=self)

    def delete_student(self):
        sid = self._get_selected_student_id()
        if not sid: return
        try: student = self.student_service.get(sid)
        except Exception as e:
            messagebox.showerror("Student Error", str(e), parent=self); return
        if not messagebox.askyesno("Delete Student",
            f"Delete {student[1]} {student[2]} ({sid})?\n\n"
            "This will also remove the student's enrollments and related scores/grades.",
            parent=self): return
        try:
            self.student_service.delete(sid)
            self.refresh_students()
            messagebox.showinfo("Deleted", "Student deleted successfully.", parent=self)
        except Exception as e: messagebox.showerror("Delete Error", str(e), parent=self)

    def open_student_dialog(self, student=None):
        editing = student is not None
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Student" if editing else "Add Student")
        dialog.geometry("470x455")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="EDIT STUDENT" if editing else "ADD STUDENT",
                     text_color=ACCENT, font=("Segoe UI", 16, "bold")).pack(
                         anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(dialog, text="Enter the student's information.",
                     text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=24, pady=(0, 15))
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24)
        fields = [("Student ID", student[0] if editing else ""), ("First Name", student[1] if editing else ""),
                  ("Last Name", student[2] if editing else ""), ("Email", student[3] if editing else ""),
                  ("Program", student[4] if editing else ""), ("Status", student[5] if editing else "Active")]
        vars_ = {}
        for label, value in fields:
            ctk.CTkLabel(frame, text=label, text_color=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(4, 2))
            var = tk.StringVar(value=value); vars_[label] = var
            entry = ctk.CTkEntry(frame, textvariable=var, height=34, corner_radius=7,
                                 fg_color=PANEL_2, border_color=BORDER)
            entry.pack(fill="x", pady=(0, 5))
            if editing and label == "Student ID": entry.configure(state="disabled")
        def save():
            v = {label: vars_[label].get().strip() for label, _ in fields}
            try:
                self.student_service.save(v["Student ID"], v["First Name"], v["Last Name"],
                                          v["Email"], v["Program"], v["Status"])
                dialog.destroy(); self.refresh_students()
                messagebox.showinfo("Saved", "Student information saved successfully.", parent=self)
            except Exception as e: messagebox.showerror("Save Error", str(e), parent=dialog)
        ctk.CTkButton(dialog, text="SAVE STUDENT", command=save, height=38,
                      corner_radius=8, fg_color=ACCENT, hover_color=HOVER,
                      text_color=BG, font=("Segoe UI", 9, "bold")).pack(fill="x", padx=24, pady=18)

    def on_student_selected(self, event=None):
        selected = self.student_tree.selection()
        if not selected: return
        sid = self.student_tree.item(selected[0], "values")[0]
        try:
            s = self.student_service.get(sid)
            self.info_var.set(f"ID: {s[0]}\nName: {s[1]} {s[2]}\nEmail: {s[3]}\nProgram: {s[4]}\nStatus: {s[5]}")
            self.load_enrollments(sid)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self)

    def load_enrollments(self, sid):
        self.enrollments = self.enrollment_service.get_by_student(sid)
        self.enrollment_count_var.set(str(len(self.enrollments)))
        values = [f"{r[0]} | {r[11]} - {r[12]} | {r[5]} | {r[2]}" for r in self.enrollments]
        self.enrollment_combo.configure(values=values)
        if values:
            self.enrollment_combo.set(values[0]); self.show_enrollment(self.enrollments[0])
        else:
            self.enrollment_combo.set(""); self.current_enrollment_id = None
            self.clear_grade_view("No enrollments found.")

    def refresh_enrollments(self):
        selected = self.student_tree.selection()
        if selected: self.load_enrollments(self.student_tree.item(selected[0], "values")[0])

    def on_enrollment_selected(self, value=None):
        values = list(self.enrollment_combo.cget("values"))
        if value in values: self.show_enrollment(self.enrollments[values.index(value)])

    def show_enrollment(self, enrollment):
        self.current_enrollment_id = enrollment[0]
        self.status_card_var.set(str(enrollment[2]))
        try: breakdown = self.grading_service.get_grade_breakdown(enrollment[0])
        except ValueError:
            self.clear_grade_view("No complete grading data yet."); return
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self); return
        self.grade_tree.delete(*self.grade_tree.get_children())
        self.final_grade_var.set(f"Final Grade: {breakdown['final_grade']:.2f}%")
        self.final_grade_card_var.set(f"{breakdown['final_grade']:.2f}%")
        self.weight_var.set(f"Total Weight: {breakdown['total_weight']:.2f}%")
        for cat in breakdown["categories"]:
            for comp in cat["components"]:
                self.grade_tree.insert("", "end", values=(
                    cat["percentage_id"], comp["component"],
                    f"{comp['score']:.2f} / {comp['max_score']:.2f}",
                    f"{comp['percentage_score']:.2f}%", f"{cat['weight']:.2f}%",
                    f"{cat['weighted_grade']:.2f}"))

    def clear_grade_view(self, message=""):
        self.grade_tree.delete(*self.grade_tree.get_children())
        self.final_grade_var.set("Final Grade: --")
        self.final_grade_card_var.set("--")
        self.status_card_var.set("--")
        self.weight_var.set(message)

    def calculate_grade(self):
        if not self.current_enrollment_id:
            messagebox.showwarning("No Enrollment", "Select an enrollment first.", parent=self); return
        try:
            grade = self.grading_service.calculate_and_save_grade(self.current_enrollment_id)
            messagebox.showinfo("Grade Saved", f"Final grade: {grade:.2f}%", parent=self)
            self.show_enrollment(self.enrollments[self.enrollment_combo.cget("values").index(self.enrollment_combo.get())])
        except Exception as e: messagebox.showerror("Grade Error", str(e), parent=self)

    def open_score_dialog(self):
        eid = self.current_enrollment_id
        if not eid:
            messagebox.showwarning("No Enrollment", "Select an enrollment first.", parent=self); return
        try:
            scores = self.score_service.get_scores(eid)
            enrollment = next(x for x in self.enrollments if x[0] == eid)
            components = self.component_repository.find_by_offering_id(enrollment[3])
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self); return
        if not components:
            messagebox.showwarning("No Components", "No grade components exist for this class offering.", parent=self); return

        existing = {r[4]: r for r in scores}
        dialog = ctk.CTkToplevel(self)
        dialog.title("Record / Update Score"); dialog.geometry("560x445")
        dialog.resizable(False, False); dialog.transient(self); dialog.grab_set()
        ctk.CTkLabel(dialog, text="RECORD / UPDATE SCORE", text_color=ACCENT,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(dialog, text=f"Enrollment: {eid}", text_color=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=24, pady=(0, 15))
        frame = ctk.CTkFrame(dialog, fg_color="transparent"); frame.pack(fill="both", expand=True, padx=24)
        ctk.CTkLabel(frame, text="Component", text_color=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        combo = ctk.CTkComboBox(frame, state="readonly", height=36, corner_radius=8,
                                fg_color=PANEL_2, border_color=BORDER, button_color=PANEL_2,
                                button_hover_color=ACCENT, dropdown_fg_color=PANEL_2)
        combo.pack(fill="x", pady=(4, 12))
        cmap = {f"{c[0]} | {c[1]} | Max {float(c[3]):.2f}": c for c in components}
        combo.configure(values=list(cmap))
        score = tk.StringVar(); remarks = tk.StringVar()
        for label, var in [("Score", score), ("Remarks", remarks)]:
            ctk.CTkLabel(frame, text=label, text_color=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            ctk.CTkEntry(frame, textvariable=var, height=36, corner_radius=8,
                         fg_color=PANEL_2, border_color=BORDER).pack(fill="x", pady=(4, 12))
        def load(value=None):
            c = cmap.get(combo.get())
            if c and c[0] in existing:
                score.set(str(existing[c[0]][1])); remarks.set(existing[c[0]][2] or "")
            else: score.set(""); remarks.set("")
        combo.configure(command=load); combo.set(list(cmap)[0]); load()
        def save():
            c = cmap.get(combo.get())
            if not c: messagebox.showwarning("Missing Component", "Select a component.", parent=dialog); return
            if not score.get().strip(): messagebox.showwarning("Missing Score", "Enter a score.", parent=dialog); return
            row = existing.get(c[0]); score_id = row[0] if row else f"SC-{eid}-{c[0]}"
            try:
                self.score_service.record_score(score_id=score_id, enrollment_id=eid,
                                                component_id=c[0], score=score.get(), remarks=remarks.get())
                dialog.destroy(); self.show_enrollment(enrollment)
                messagebox.showinfo("Saved", "Score saved successfully.", parent=self)
            except Exception as e: messagebox.showerror("Score Error", str(e), parent=dialog)
        ctk.CTkButton(dialog, text="SAVE SCORE", command=save, height=38, corner_radius=8,
                      fg_color=ACCENT, hover_color=HOVER, text_color=BG,
                      font=("Segoe UI", 9, "bold")).pack(fill="x", padx=24, pady=18)


def run():
    app = StudentGradingGUI()
    app.mainloop()


if __name__ == "__main__":
    run()
