import tkinter as tk
from tkinter import messagebox, ttk

from app.repositories.grade_component_repository import GradeComponentRepository
from app.gui.academic_window import AcademicWindow
from app.gui.enrollment_window import EnrollmentWindow
from app.gui.student_report_window import StudentReportWindow
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService


class StudentGradingGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Student Information and Grading System")
        self.geometry("1200x720")
        self.minsize(1000, 620)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()
        self.component_repository = GradeComponentRepository()

        self.enrollments = []
        self.current_enrollment_id = None

        self._configure_style()
        self._build_ui()
        self.refresh_students()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        header = ttk.Frame(self, padding=(18, 15, 18, 10))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Student Information and Grading System",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Button(
            header,
            text="Refresh",
            command=self.refresh_students
        ).pack(side="right")

        body = ttk.Frame(self, padding=(18, 0, 18, 18))
        body.pack(fill="both", expand=True)

        left = ttk.LabelFrame(
            body,
            text="Students",
            style="Section.TLabelframe",
            padding=10
        )
        left.pack(side="left", fill="y")

        self.student_tree = ttk.Treeview(
            left,
            columns=("id", "name", "program", "status"),
            show="headings",
            selectmode="browse",
            height=22
        )

        for column, title, width in [
            ("id", "ID", 85),
            ("name", "Name", 180),
            ("program", "Program", 95),
            ("status", "Status", 85)
        ]:
            self.student_tree.heading(column, text=title)
            self.student_tree.column(column, width=width, anchor="w")

        student_scroll = ttk.Scrollbar(
            left,
            orient="vertical",
            command=self.student_tree.yview
        )
        self.student_tree.configure(yscrollcommand=student_scroll.set)
        self.student_tree.pack(side="left", fill="y")
        student_scroll.pack(side="right", fill="y")
        self.student_tree.bind(
            "<<TreeviewSelect>>",
            self.on_student_selected
        )

        student_actions = ttk.Frame(left, padding=(0, 10, 0, 0))
        student_actions.pack(fill="x")

        ttk.Button(
            student_actions,
            text="Add",
            command=self.add_student
        ).pack(side="left", expand=True, fill="x")

        ttk.Button(
            student_actions,
            text="Edit",
            command=self.edit_student
        ).pack(side="left", expand=True, fill="x", padx=4)

        ttk.Button(
            student_actions,
            text="Delete",
            command=self.delete_student
        ).pack(side="left", expand=True, fill="x")

        right = ttk.Frame(body, padding=(15, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        info_frame = ttk.LabelFrame(
            right,
            text="Student Information",
            style="Section.TLabelframe",
            padding=12
        )
        info_frame.pack(fill="x")

        self.info_var = tk.StringVar(value="Select a student.")
        ttk.Label(
            info_frame,
            textvariable=self.info_var,
            justify="left"
        ).pack(anchor="w")

        enrollment_frame = ttk.LabelFrame(
            right,
            text="Enrollment",
            style="Section.TLabelframe",
            padding=10
        )
        enrollment_frame.pack(fill="x", pady=10)

        self.enrollment_combo = ttk.Combobox(
            enrollment_frame,
            state="readonly"
        )
        self.enrollment_combo.pack(
            side="left",
            fill="x",
            expand=True
        )
        self.enrollment_combo.bind(
            "<<ComboboxSelected>>",
            self.on_enrollment_selected
        )

        ttk.Button(
            enrollment_frame,
            text="Refresh",
            command=self.refresh_enrollments
        ).pack(side="left", padx=(8, 0))

        grade_frame = ttk.LabelFrame(
            right,
            text="Grade Breakdown",
            style="Section.TLabelframe",
            padding=10
        )
        grade_frame.pack(fill="both", expand=True)

        summary = ttk.Frame(grade_frame)
        summary.pack(fill="x", pady=(0, 10))

        self.final_grade_var = tk.StringVar(value="Final Grade: --")
        self.weight_var = tk.StringVar(value="Total Weight: --")

        ttk.Label(
            summary,
            textvariable=self.final_grade_var,
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")

        ttk.Label(
            summary,
            textvariable=self.weight_var
        ).pack(side="right")

        table_frame = ttk.Frame(grade_frame)
        table_frame.pack(fill="both", expand=True)

        self.grade_tree = ttk.Treeview(
            table_frame,
            columns=("category", "component", "score", "percentage", "weight", "weighted"),
            show="headings"
        )

        columns = [
            ("category", "Category", 85),
            ("component", "Component", 180),
            ("score", "Score", 110),
            ("percentage", "Percentage", 100),
            ("weight", "Weight", 85),
            ("weighted", "Weighted", 100)
        ]

        for column, title, width in columns:
            self.grade_tree.heading(column, text=title)
            self.grade_tree.column(column, width=width, anchor="w")

        grade_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.grade_tree.yview
        )
        self.grade_tree.configure(yscrollcommand=grade_scroll.set)
        self.grade_tree.pack(side="left", fill="both", expand=True)
        grade_scroll.pack(side="right", fill="y")

        actions = ttk.Frame(right, padding=(0, 10, 0, 0))
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Record / Update Score",
            command=self.open_score_dialog
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Student Report",
            command=self.open_student_report
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="Calculate & Save Grade",
            command=self.calculate_grade
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="Academic Management",
            command=self.open_academic_management
        ).pack(side="right")

        ttk.Button(
            actions,
            text="Enrollment Management",
            command=self.open_enrollment_management
        ).pack(side="right", padx=(0, 8))

    def open_academic_management(self):
        AcademicWindow(self)

    def open_enrollment_management(self):
        EnrollmentWindow(self)

    def open_student_report(self):
        student_id = self._get_selected_student_id()
        if student_id:
            StudentReportWindow(self, student_id)

    def refresh_students(self):
        try:
            students = self.student_service.get_all()
            self.student_tree.delete(*self.student_tree.get_children())

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
