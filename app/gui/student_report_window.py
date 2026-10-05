import tkinter as tk
from tkinter import messagebox, ttk

from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.student_service import StudentService


class StudentReportWindow(ttk.Frame):
    def __init__(self, parent, student_id):
        super().__init__(parent)

        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.grading_service = GradingService()

        self.student_id = student_id

        self._configure_style()
        self._build_ui()
        self.load_report()

    def _configure_style(self):
        style = ttk.Style(self)
        style.configure("ReportTitle.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("ReportSection.TLabelframe.Label",
                        font=("Segoe UI", 10, "bold"))
        style.configure("ReportTreeview", rowheight=28)
        style.configure("ReportTreeview.Heading",
                        font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)

        self.title_var = tk.StringVar(value="Student Academic Report")
        ttk.Label(
            frame,
            textvariable=self.title_var,
            style="ReportTitle.TLabel"
        ).pack(anchor="w")

        self.student_var = tk.StringVar()
        ttk.Label(
            frame,
            textvariable=self.student_var,
            justify="left"
        ).pack(anchor="w", pady=(8, 15))

        report_frame = ttk.LabelFrame(
            frame,
            text="Academic Record",
            style="ReportSection.TLabelframe",
            padding=10
        )
        report_frame.pack(fill="both", expand=True)

        table_frame = ttk.Frame(report_frame)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame,
            columns=(
                "enrollment",
                "subject",
                "class",
                "section",
                "semester",
                "status",
                "grade"
            ),
            show="headings",
            style="Treeview"
        )

        columns = [
            ("enrollment", "Enrollment", 100),
            ("subject", "Subject", 180),
            ("class", "Class", 90),
            ("section", "Section", 90),
            ("semester", "Semester", 110),
            ("status", "Status", 100),
            ("grade", "Final Grade", 100)
        ]

        for column, heading, width in columns:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.summary_var = tk.StringVar()
        ttk.Label(
            frame,
            textvariable=self.summary_var,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(12, 0))

        ttk.Button(
            frame,
            text="Refresh Report",
            command=self.load_report
        ).pack(anchor="e", pady=(10, 0))

    def load_report(self):
        try:
            student = self.student_service.get(self.student_id)
            enrollments = self.enrollment_service.get_by_student(
                self.student_id
            )

            self.title_var.set(
                f"Academic Report - {student[1]} {student[2]}"
            )
            self.student_var.set(
                f"Student ID: {student[0]}\n"
                f"Email: {student[3]}\n"
                f"Program: {student[4]}\n"
                f"Status: {student[5]}"
            )

            self.tree.delete(*self.tree.get_children())

            graded_count = 0
            grade_total = 0.0

            for enrollment in enrollments:
                saved_grade = self.grading_service.get_saved_grade(
                    enrollment[0]
                )

                if saved_grade:
                    grade_text = f"{float(saved_grade[1]):.2f}%"
                    grade_total += float(saved_grade[1])
                    graded_count += 1
                else:
                    try:
                        calculated_grade = self.grading_service.calculate_grade(
                            enrollment[0]
                        )
                        grade_text = f"{calculated_grade:.2f}% (Calculated)"
                        grade_total += float(calculated_grade)
                        graded_count += 1
                    except ValueError:
                        grade_text = "No grade yet"

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        enrollment[0],
                        f"{enrollment[11]} - {enrollment[12]}",
                        enrollment[4],
                        enrollment[6],
                        enrollment[8],
                        enrollment[2],
                        grade_text
                    )
                )

            if not enrollments:
                self.summary_var.set("No enrollments found.")
            elif graded_count:
                average = grade_total / graded_count
                self.summary_var.set(
                    f"Enrollments: {len(enrollments)}    "
                    f"Grades Available: {graded_count}    "
                    f"Average: {average:.2f}%"
                )
            else:
                self.summary_var.set(
                    f"Enrollments: {len(enrollments)}    "
                    "No grades available yet."
                )

        except Exception as error:
            messagebox.showerror(
                "Report Error",
                str(error),
                parent=self
            )
