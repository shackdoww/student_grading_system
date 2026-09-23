import tkinter as tk
from tkinter import messagebox, ttk

from app.services.grading_service import GradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService
from app.services.enrollment_service import EnrollmentService


class StudentGradingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Information and Grading System")
        self.geometry("1050x650")
        self.minsize(900, 550)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()

        self._build_ui()
        self.refresh_students()

    def _build_ui(self):
        header = ttk.Frame(self, padding=15)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Student Information and Grading System",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")

        body = ttk.Frame(self, padding=(15, 0, 15, 15))
        body.pack(fill="both", expand=True)

        left = ttk.LabelFrame(body, text="Students", padding=10)
        left.pack(side="left", fill="y")

        self.student_tree = ttk.Treeview(
            left,
            columns=("id", "name", "program", "status"),
            show="headings",
            height=22
        )
        for column, title, width in [
            ("id", "ID", 90),
            ("name", "Name", 180),
            ("program", "Program", 90),
            ("status", "Status", 90)
        ]:
            self.student_tree.heading(column, text=title)
            self.student_tree.column(column, width=width)

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        self.student_tree.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_selected)

        right = ttk.Frame(body, padding=(15, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        self.student_info = ttk.LabelFrame(right, text="Student Information", padding=10)
        self.student_info.pack(fill="x")

        self.info_var = tk.StringVar(value="Select a student.")
        ttk.Label(
            self.student_info,
            textvariable=self.info_var,
            justify="left"
        ).pack(anchor="w")

        enroll_frame = ttk.LabelFrame(right, text="Enrollments", padding=10)
        enroll_frame.pack(fill="x", pady=10)

        self.enrollment_combo = ttk.Combobox(
            enroll_frame,
            state="readonly",
            width=70
        )
        self.enrollment_combo.pack(side="left", fill="x", expand=True)
        self.enrollment_combo.bind("<<ComboboxSelected>>", self.on_enrollment_selected)

        ttk.Button(
            enroll_frame,
            text="Refresh",
            command=self.refresh_enrollments
        ).pack(side="left", padx=(8, 0))

        self.grade_frame = ttk.LabelFrame(right, text="Grade Information", padding=10)
        self.grade_frame.pack(fill="both", expand=True)

        self.grade_text = tk.Text(
            self.grade_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 10)
        )
        self.grade_text.pack(fill="both", expand=True)

        actions = ttk.Frame(right, padding=(0, 10, 0, 0))
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Record / Update Score",
            command=self.open_score_dialog
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Calculate & Save Grade",
            command=self.calculate_grade
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="Refresh Students",
            command=self.refresh_students
        ).pack(side="right")

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
        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def on_student_selected(self, event=None):
        selected = self.student_tree.selection()
        if not selected:
            return

        student_id = self.student_tree.item(selected[0], "values")[0]

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
            f"{row[0]} | {row[11]} - {row[12]} | {row[5]} | {row[2]}"
            for row in enrollments
        ]

        if enrollments:
            self.enrollment_combo.current(0)
            self.show_enrollment(enrollments[0])
        else:
            self.enrollment_combo.set("")
            self.clear_grade_view()

    def refresh_enrollments(self):
        selected = self.student_tree.selection()
        if selected:
            student_id = self.student_tree.item(selected[0], "values")[0]
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

        lines = [
            f"Enrollment: {self.current_enrollment_id}",
            "",
            f"Final Grade: {breakdown['final_grade']:.2f}%",
            f"Total Weight: {breakdown['total_weight']:.2f}%",
            "",
            "Grade Breakdown",
            "---------------"
        ]

        for category in breakdown["categories"]:
            lines.append(
                f"{category['percentage_id']}: "
                f"{category['average']:.2f}% average × "
                f"{category['weight']:.2f}% = "
                f"{category['weighted_grade']:.2f}"
            )

            for component in category["components"]:
                lines.append(
                    f"  {component['component']}: "
                    f"{component['score']:.2f}/{component['max_score']:.2f} "
                    f"({component['percentage_score']:.2f}%)"
                )

        self.set_grade_text("\n".join(lines))

    def clear_grade_view(self, message=""):
        self.set_grade_text(message)

    def set_grade_text(self, text):
        self.grade_text.configure(state="normal")
        self.grade_text.delete("1.0", "end")
        self.grade_text.insert("1.0", text)
        self.grade_text.configure(state="disabled")

    def calculate_grade(self):
        enrollment_id = getattr(self, "current_enrollment_id", None)

        if not enrollment_id:
            messagebox.showwarning("No Enrollment", "Select an enrollment first.")
            return

        try:
            final_grade = self.grading_service.calculate_and_save_grade(
                enrollment_id
            )
            messagebox.showinfo(
                "Grade Saved",
                f"Final grade: {final_grade:.2f}%"
            )
            self.show_enrollment(
                next(row for row in self.enrollments if row[0] == enrollment_id)
            )
        except Exception as error:
            messagebox.showerror("Grade Error", str(error))

    def open_score_dialog(self):
        enrollment_id = getattr(self, "current_enrollment_id", None)

        if not enrollment_id:
            messagebox.showwarning("No Enrollment", "Select an enrollment first.")
            return

        try:
            scores = self.score_service.get_scores(enrollment_id)
        except Exception as error:
            messagebox.showerror("Database Error", str(error))
            return

        dialog = tk.Toplevel(self)
        dialog.title("Record / Update Score")
        dialog.geometry("520x420")
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Component").pack(anchor="w")
        component_combo = ttk.Combobox(frame, state="readonly", width=60)
        component_combo.pack(fill="x", pady=(3, 10))

        components = {}
        for score_row in scores:
            label = (
                f"{score_row[4]} | {score_row[5]} | "
                f"Max {float(score_row[7]):.2f}"
            )
            components[label] = score_row
        component_combo["values"] = list(components.keys())

        ttk.Label(frame, text="Score").pack(anchor="w")
        score_var = tk.StringVar()
        ttk.Entry(frame, textvariable=score_var).pack(fill="x", pady=(3, 10))

        ttk.Label(frame, text="Remarks").pack(anchor="w")
        remarks_var = tk.StringVar()
        ttk.Entry(frame, textvariable=remarks_var).pack(fill="x", pady=(3, 10))

        def save():
            if not component_combo.get():
                messagebox.showwarning("Missing Component", "Select a component.")
                return

            row = components[component_combo.get()]

            try:
                self.score_service.record_score(
                    score_id=row[0],
                    enrollment_id=enrollment_id,
                    component_id=row[4],
                    score=score_var.get(),
                    remarks=remarks_var.get()
                )
                dialog.destroy()
                self.show_enrollment(
                    next(item for item in self.enrollments if item[0] == enrollment_id)
                )
                messagebox.showinfo("Saved", "Score saved successfully.")
            except Exception as error:
                messagebox.showerror("Score Error", str(error))

        if scores:
            component_combo.current(0)
            first = scores[0]
            score_var.set(str(first[1]))
            remarks_var.set(first[2] or "")

        ttk.Button(frame, text="Save Score", command=save).pack(pady=15)


def run():
    app = StudentGradingGUI()
    app.mainloop()
