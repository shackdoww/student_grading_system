import tkinter as tk
from tkinter import messagebox, ttk

from app.repositories.grade_component_repository import GradeComponentRepository
from app.gui.academic_window import AcademicWindow
from app.gui.enrollment_window import EnrollmentWindow
from app.gui.student_report_window import StudentReportWindow
from app.gui.class_roster_window import ClassRosterWindow
from app.gui.class_grade_window import ClassGradeWindow
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService
from app.gui.theme import apply_theme


class StudentGradingGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Student Information and Grading System")
        self._setup_dpi()
        self.geometry("1000x620")
        self.minsize(850, 520)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()
        self.component_repository = GradeComponentRepository()

        self.enrollments = []
        self.current_enrollment_id = None

        apply_theme(self)
        self._configure_style()
        self._build_ui()
        self.bind("<Configure>", self._on_resize)
        self.refresh_students()

    def _setup_dpi(self):
        try:
            dpi = self.winfo_fpixels("1i")
            self.tk.call("tk", "scaling", max(1.0, min(1.5, dpi / 96.0)))
        except tk.TclError:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))

    def _build_ui(self):
        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg="#0B1015", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="OW", bg="#0B1015", fg="#F99E1A",
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w", padx=18, pady=(20, 0))

        tk.Label(
            sidebar, text="ACADEMIC\nCOMMAND CENTER",
            bg="#0B1015", fg="#F2F2F2",
            justify="left", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 24))

        tk.Label(
            sidebar, text="MAIN MENU", bg="#0B1015", fg="#66737E",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 6))

        def nav_button(text, command, active=False):
            bg = "#F99E1A" if active else "#0B1015"
            fg = "#111820" if active else "#D5DCE1"
            btn = tk.Button(
                sidebar, text=text, command=command, anchor="w",
                bg=bg, fg=fg, activebackground="#F99E1A",
                activeforeground="#111820", relief="flat", bd=0,
                font=("Segoe UI", 9, "bold"), padx=18, pady=9,
                cursor="hand2"
            )
            btn.pack(fill="x", padx=10, pady=2)
            return btn

        nav_button("▣   Dashboard", lambda: None, True)
        nav_button("●   Students", self.focus_students)
        nav_button("▤   Class Grades", self.open_class_grades)
        nav_button("▥   Reports", self.open_student_report)
        nav_button("⚙   Academic", self.open_academic_management)
        nav_button("▦   Enrollments", self.open_enrollment_management)

        tk.Frame(sidebar, bg="#27323B", height=1).pack(fill="x", padx=16, pady=18)

        tk.Label(
            sidebar, text="SYSTEM", bg="#0B1015", fg="#66737E",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 6))

        nav_button("⟳   Refresh Data", self.refresh_students)

        tk.Label(
            sidebar, text="Student Information\nand Grading System",
            bg="#0B1015", fg="#66737E", justify="left",
            font=("Segoe UI", 7)
        ).pack(side="bottom", anchor="w", padx=18, pady=16)

        content = tk.Frame(shell, bg="#111820")
        content.pack(side="left", fill="both", expand=True)

        top = tk.Frame(content, bg="#111820")
        top.pack(fill="x", padx=22, pady=(18, 12))

        tk.Label(
            top, text="Dashboard", bg="#111820", fg="#F2F2F2",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")

        tk.Label(
            top, text="  /  STUDENT OVERVIEW", bg="#111820", fg="#7E8A94",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", pady=(7, 0))

        tk.Button(
            top, text="⟳", command=self.refresh_students,
            bg="#222E38", fg="#F99E1A", activebackground="#F99E1A",
            activeforeground="#111820", relief="flat", bd=0,
            font=("Segoe UI", 13, "bold"), width=3, cursor="hand2"
        ).pack(side="right")

        cards = tk.Frame(content, bg="#111820")
        cards.pack(fill="x", padx=22, pady=(0, 12))

        def card(parent, title, variable):
            box = tk.Frame(parent, bg="#1B252E", highlightbackground="#35424D",
                           highlightthickness=1)
            box.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(box, text=title.upper(), bg="#1B252E", fg="#7E8A94",
                     font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=12, pady=(9, 0))
            tk.Label(box, textvariable=variable, bg="#1B252E", fg="#F2F2F2",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=(1, 8))
            return box

        self.student_count_var = tk.StringVar(value="0")
        self.enrollment_count_var = tk.StringVar(value="0")
        self.final_grade_card_var = tk.StringVar(value="--")
        self.status_card_var = tk.StringVar(value="--")

        card(cards, "Students", self.student_count_var)
        card(cards, "Enrollments", self.enrollment_count_var)
        card(cards, "Current Grade", self.final_grade_card_var)
        card(cards, "Status", self.status_card_var)

        workspace = tk.Frame(content, bg="#111820")
        workspace.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        left = tk.Frame(workspace, bg="#1B252E", highlightbackground="#35424D",
                        highlightthickness=1, width=330)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="STUDENTS", bg="#1B252E", fg="#F99E1A",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self.student_tree = ttk.Treeview(
            left, columns=("id", "name", "program", "status"),
            show="headings", selectmode="browse", height=10
        )
        for column, title, width in [
            ("id", "ID", 55), ("name", "Name", 125),
            ("program", "Program", 75), ("status", "Status", 65)
        ]:
            self.student_tree.heading(column, text=title)
            self.student_tree.column(column, width=width, anchor="w", stretch=(column != "id"))
        self.student_tree.pack(fill="both", expand=True, padx=8)
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)
        self.student_tree.bind("<Double-1>", self.on_student_selected)

        student_actions = ttk.Frame(left)
        student_actions.pack(fill="x", padx=8, pady=8)
        for text, command in [
            ("ADD", self.add_student), ("EDIT", self.edit_student),
            ("DELETE", self.delete_student)
        ]:
            ttk.Button(student_actions, text=text, command=command).pack(
                side="left", fill="x", expand=True, padx=2
            )

        right = tk.Frame(workspace, bg="#1B252E", highlightbackground="#35424D",
                         highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        info = tk.Frame(right, bg="#1B252E")
        info.pack(fill="x", padx=14, pady=(10, 6))

        tk.Label(info, text="SELECTED STUDENT", bg="#1B252E", fg="#F99E1A",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")

        self.info_var = tk.StringVar(value="Select a student.")
        tk.Label(info, textvariable=self.info_var, bg="#1B252E", fg="#DCE2E6",
                 justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        enrollment_frame = ttk.Frame(right)
        enrollment_frame.pack(fill="x", padx=14, pady=(4, 8))

        self.enrollment_combo = ttk.Combobox(enrollment_frame, state="readonly")
        self.enrollment_combo.pack(side="left", fill="x", expand=True)
        self.enrollment_combo.bind("<<ComboboxSelected>>", self.on_enrollment_selected)
        ttk.Button(enrollment_frame, text="↻", command=self.refresh_enrollments).pack(
            side="left", padx=(6, 0)
        )

        grade_frame = tk.Frame(right, bg="#1B252E")
        grade_frame.pack(fill="x", padx=14, pady=(0, 8))

        grade_top = tk.Frame(grade_frame, bg="#1B252E")
        grade_top.pack(fill="x", pady=(0, 5))

        tk.Label(grade_top, text="GRADE BREAKDOWN", bg="#1B252E", fg="#F99E1A",
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self.final_grade_var = tk.StringVar(value="Final Grade: --")
        self.weight_var = tk.StringVar(value="Total Weight: --")
        tk.Label(grade_top, textvariable=self.final_grade_var, bg="#1B252E",
                 fg="#F2F2F2", font=("Segoe UI", 11, "bold")).pack(side="right")
        tk.Label(grade_top, textvariable=self.weight_var, bg="#1B252E",
                 fg="#7E8A94", font=("Segoe UI", 8)).pack(side="right", padx=12)

        table_frame = tk.Frame(grade_frame, bg="#1B252E")
        table_frame.pack(fill="x")

        self.grade_tree = ttk.Treeview(
            table_frame,
            columns=("category", "component", "score", "percentage", "weight", "weighted"),
            show="headings", height=6
        )
        for column, title, width in [
            ("category", "Cat.", 48), ("component", "Component", 120),
            ("score", "Score", 85), ("percentage", "%", 65),
            ("weight", "Weight", 65), ("weighted", "Weighted", 75)
        ]:
            self.grade_tree.heading(column, text=title)
            self.grade_tree.column(column, width=width, anchor="w")
        self.grade_tree.pack(fill="x")

        actions = ttk.Frame(right)
        actions.pack(fill="x", padx=12, pady=(4, 10))

        for text, command, style in [
            ("RECORD SCORE", self.open_score_dialog, None),
            ("SAVE GRADE", self.calculate_grade, "Accent.TButton"),
            ("CLASS GRADES", self.open_class_grades, "Accent.TButton"),
            ("STUDENT REPORT", self.open_student_report, None),
            ("CLASS / SECTION", self.open_class_roster, None)
        ]:
            kwargs = {"text": text, "command": command}
            if style:
                kwargs["style"] = style
            ttk.Button(actions, **kwargs).pack(side="left", padx=2)

    def _on_resize(self, event=None):
        if event is None or event.widget is not self:
            return
        if hasattr(self, "student_tree"):
            panel_width = max(260, int(self.winfo_width() * 0.30))
            self.student_tree.column("name", width=max(110, panel_width - 185))

    def focus_students(self):
        self.student_tree.focus_set()
        items = self.student_tree.get_children()
        if items:
            current = self.student_tree.selection()
            item = current[0] if current else items[0]
            self.student_tree.selection_set(item)
            self.student_tree.focus(item)
            self.student_tree.see(item)
            self.on_student_selected()

    def open_academic_management(self):
        AcademicWindow(self)

    def open_enrollment_management(self):
        EnrollmentWindow(self)

    def open_class_grades(self):
        try:
            ClassGradeWindow(self)
        except Exception as error:
            messagebox.showerror(
                "Grade Management Error",
                f"Unable to open Class Grade Management.\n\n{error}"
            )

    def open_class_roster(self):
        try:
            ClassRosterWindow(self)
        except Exception as error:
            messagebox.showerror(
                "Class View Error",
                f"Unable to open the Class / Section View.\n\n{error}"
            )

    def open_student_report(self):
        student_id = self._get_selected_student_id()

        if not student_id:
            return

        try:
            StudentReportWindow(self, student_id)
        except Exception as error:
            messagebox.showerror(
                "Student Report Error",
                f"Unable to open the Student Academic Report.\n\n{error}"
            )

    def refresh_students(self):
        try:
            students = self.student_service.get_all()
            self.student_tree.delete(*self.student_tree.get_children())

            self.student_count_var.set(str(len(students)))

            for student in students:
                self.student_tree.insert(
                    "",
                    "end",
                    values=(
                        student[0],
                        f"{student[1]} {student[2]}",
                        student[4],
                        student[5]
                    )
                )

            if students:
                first = self.student_tree.get_children()[0]
                self.student_tree.selection_set(first)
                self.student_tree.focus(first)
                self.on_student_selected()
            else:
                self.info_var.set("No students found.")
                self.enrollment_combo.set("")
                self.clear_grade_view()

        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def _get_selected_student_id(self):
        selected = self.student_tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Student Selected",
                "Select a student first."
            )
            return None

        return self.student_tree.item(
            selected[0],
            "values"
        )[0]

    def add_student(self):
        self.open_student_dialog()

    def edit_student(self):
        student_id = self._get_selected_student_id()

        if student_id:
            try:
                student = self.student_service.get(student_id)
                self.open_student_dialog(student)
            except Exception as error:
                messagebox.showerror("Student Error", str(error))

    def delete_student(self):
        student_id = self._get_selected_student_id()

        if not student_id:
            return

        try:
            student = self.student_service.get(student_id)
        except Exception as error:
            messagebox.showerror("Student Error", str(error))
            return

        confirmed = messagebox.askyesno(
            "Delete Student",
            f"Delete {student[1]} {student[2]} ({student_id})?\n\n"
            "This will also remove the student's enrollments and related "
            "scores/grades because of the database relationships."
        )

        if not confirmed:
            return

        try:
            self.student_service.delete(student_id)
            self.refresh_students()
            messagebox.showinfo("Deleted", "Student deleted successfully.")
        except Exception as error:
            messagebox.showerror("Delete Error", str(error))

    def open_student_dialog(self, student=None):
        editing = student is not None

        dialog = tk.Toplevel(self)
        dialog.title("Edit Student" if editing else "Add Student")
        dialog.geometry("460x430")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Student ID", student[0] if editing else ""),
            ("First Name", student[1] if editing else ""),
            ("Last Name", student[2] if editing else ""),
            ("Email", student[3] if editing else ""),
            ("Program", student[4] if editing else ""),
            ("Status", student[5] if editing else "Active")
        ]

        variables = {}

        for label, value in fields:
            ttk.Label(frame, text=label).pack(anchor="w", pady=(4, 2))

            variable = tk.StringVar(value=value)
            variables[label] = variable

            entry = ttk.Entry(frame, textvariable=variable)

            if editing and label == "Student ID":
                entry.configure(state="disabled")

            entry.pack(fill="x", pady=(0, 5))

        def save():
            values = {
                label: variables[label].get().strip()
                for label, _ in fields
            }

            try:
                self.student_service.save(
                    values["Student ID"],
                    values["First Name"],
                    values["Last Name"],
                    values["Email"],
                    values["Program"],
                    values["Status"]
                )

                dialog.destroy()
                self.refresh_students()

                messagebox.showinfo(
                    "Saved",
                    "Student information saved successfully."
                )

            except Exception as error:
                messagebox.showerror(
                    "Save Error",
                    str(error)
                )

        ttk.Button(
            frame,
            text="Save Student",
            command=save
        ).pack(fill="x", pady=(15, 0))

    def on_student_selected(self, event=None):
        selected = self.student_tree.selection()
        if not selected:
            return

        student_id = self.student_tree.item(
            selected[0],
            "values"
        )[0]

        try:
            student = self.student_service.get(student_id)

            self.info_var.set(
                f"ID: {student[0]}\n"
                f"Name: {student[1]} {student[2]}\n"
                f"Email: {student[3]}\n"
                f"Program: {student[4]}\n"
                f"Status: {student[5]}"
            )

            self.load_enrollments(student_id)

        except Exception as error:
            messagebox.showerror("Error", str(error))

    def load_enrollments(self, student_id):
        enrollments = self.enrollment_service.get_by_student(student_id)
        self.enrollments = enrollments
        self.enrollment_count_var.set(str(len(enrollments)))

        self.enrollment_combo["values"] = [
            f"{row[0]} | {row[11]} - {row[12]} | "
            f"{row[5]} | {row[2]}"
            for row in enrollments
        ]

        if enrollments:
            self.enrollment_combo.current(0)
            self.show_enrollment(enrollments[0])
        else:
            self.enrollment_combo.set("")
            self.current_enrollment_id = None
            self.clear_grade_view("No enrollments found.")

    def refresh_enrollments(self):
        selected = self.student_tree.selection()
        if selected:
            student_id = self.student_tree.item(
                selected[0],
                "values"
            )[0]
            self.load_enrollments(student_id)

    def on_enrollment_selected(self, event=None):
        index = self.enrollment_combo.current()

        if index >= 0:
            self.show_enrollment(self.enrollments[index])

    def show_enrollment(self, enrollment):
        self.current_enrollment_id = enrollment[0]
        self.status_card_var.set(str(enrollment[2]))

        try:
            breakdown = self.grading_service.get_grade_breakdown(
                self.current_enrollment_id
            )
        except ValueError:
            self.clear_grade_view("No complete grading data yet.")
            return
        except Exception as error:
            messagebox.showerror("Database Error", str(error))
            return

        self.grade_tree.delete(*self.grade_tree.get_children())

        self.final_grade_var.set(
            f"Final Grade: {breakdown['final_grade']:.2f}%"
        )
        self.final_grade_card_var.set(
            f"{breakdown['final_grade']:.2f}%"
        )
        self.weight_var.set(
            f"Total Weight: {breakdown['total_weight']:.2f}%"
        )

        for category in breakdown["categories"]:
            category_id = category["percentage_id"]

            for component in category["components"]:
                self.grade_tree.insert(
                    "",
                    "end",
                    values=(
                        category_id,
                        component["component"],
                        f"{component['score']:.2f} / {component['max_score']:.2f}",
                        f"{component['percentage_score']:.2f}%",
                        f"{category['weight']:.2f}%",
                        f"{category['weighted_grade']:.2f}"
                    )
                )

    def clear_grade_view(self, message=""):
        self.grade_tree.delete(*self.grade_tree.get_children())
        self.final_grade_var.set("Final Grade: --")
        self.final_grade_card_var.set("--")
        self.status_card_var.set("--")
        self.weight_var.set(message)

    def calculate_grade(self):
        enrollment_id = self.current_enrollment_id

        if not enrollment_id:
            messagebox.showwarning(
                "No Enrollment",
                "Select an enrollment first."
            )
            return

        try:
            final_grade = self.grading_service.calculate_and_save_grade(
                enrollment_id
            )

            messagebox.showinfo(
                "Grade Saved",
                f"Final grade: {final_grade:.2f}%"
            )

            for enrollment in self.enrollments:
                if enrollment[0] == enrollment_id:
                    self.show_enrollment(enrollment)
                    break

        except Exception as error:
            messagebox.showerror("Grade Error", str(error))

    def open_score_dialog(self):
        enrollment_id = self.current_enrollment_id

        if not enrollment_id:
            messagebox.showwarning(
                "No Enrollment",
                "Select an enrollment first."
            )
            return

        try:
            scores = self.score_service.get_scores(enrollment_id)
            enrollment = next(
                item for item in self.enrollments
                if item[0] == enrollment_id
            )
            components = self.component_repository.find_by_offering_id(
                enrollment[3]
            )

        except Exception as error:
            messagebox.showerror("Database Error", str(error))
            return

        if not components:
            messagebox.showwarning(
                "No Components",
                "No grade components exist for this class offering."
            )
            return

        existing_scores = {
            row[4]: row
            for row in scores
        }

        dialog = tk.Toplevel(self)
        dialog.title("Record / Update Score")
        dialog.geometry("540x430")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=f"Enrollment: {enrollment_id}",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(frame, text="Component").pack(anchor="w")

        component_combo = ttk.Combobox(
            frame,
            state="readonly"
        )
        component_combo.pack(fill="x", pady=(4, 12))

        component_map = {}

        for component in components:
            label = (
                f"{component[0]} | {component[1]} | "
                f"Max {float(component[3]):.2f}"
            )
            component_map[label] = component

        component_combo["values"] = list(component_map.keys())

        ttk.Label(frame, text="Score").pack(anchor="w")

        score_var = tk.StringVar()
        ttk.Entry(
            frame,
            textvariable=score_var
        ).pack(fill="x", pady=(4, 12))

        ttk.Label(frame, text="Remarks").pack(anchor="w")

        remarks_var = tk.StringVar()
        ttk.Entry(
            frame,
            textvariable=remarks_var
        ).pack(fill="x", pady=(4, 12))

        def load_selected_component(event=None):
            component = component_map.get(component_combo.get())

            if not component:
                return

            existing = existing_scores.get(component[0])

            if existing:
                score_var.set(str(existing[1]))
                remarks_var.set(existing[2] or "")
            else:
                score_var.set("")
                remarks_var.set("")

        component_combo.bind(
            "<<ComboboxSelected>>",
            load_selected_component
        )

        def save():
            component = component_map.get(component_combo.get())

            if not component:
                messagebox.showwarning(
                    "Missing Component",
                    "Select a component."
                )
                return

            if not score_var.get().strip():
                messagebox.showwarning(
                    "Missing Score",
                    "Enter a score."
                )
                return

            existing = existing_scores.get(component[0])

            if existing:
                score_id = existing[0]
            else:
                score_id = (
                    f"SC-{enrollment_id}-{component[0]}"
                )

            try:
                self.score_service.record_score(
                    score_id=score_id,
                    enrollment_id=enrollment_id,
                    component_id=component[0],
                    score=score_var.get(),
                    remarks=remarks_var.get()
                )

                dialog.destroy()

                for item in self.enrollments:
                    if item[0] == enrollment_id:
                        self.show_enrollment(item)
                        break

                messagebox.showinfo(
                    "Saved",
                    "Score saved successfully."
                )

            except Exception as error:
                messagebox.showerror(
                    "Score Error",
                    str(error)
                )

        component_combo.current(0)
        load_selected_component()

        ttk.Button(
            frame,
            text="Save Score",
            command=save
        ).pack(pady=12)


def run():
    app = StudentGradingGUI()
    app.mainloop()


if __name__ == "__main__":
    run()
