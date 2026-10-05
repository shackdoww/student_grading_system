import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk

from app.services.academic_service import AcademicService
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService


class ClassRosterWindow(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F6F4FB", corner_radius=0)

        self.academic_service = AcademicService()
        self.enrollment_service = EnrollmentService()
        self.grading_service = GradingService()
        self.offerings = []
        self.roster = []

        self._build_ui()
        self.refresh_offerings()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=22)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Class / Section View",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Select a class offering to view its enrolled students and grades.").pack(
            anchor="w", pady=(5, 12))

        selection = ttk.Frame(frame)
        selection.pack(fill="x", pady=(0, 12))
        ttk.Label(selection, text="Class Offering:").pack(side="left")

        self.offering_combo = ttk.Combobox(selection, state="readonly")
        self.offering_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.offering_combo.bind("<<ComboboxSelected>>", self.on_offering_selected)

        ttk.Button(selection, text="Refresh", command=self.refresh_offerings).pack(side="left")

        info_frame = ttk.LabelFrame(frame, text="Class Information", padding=10)
        info_frame.pack(fill="x", pady=(0, 12))
        self.info_var = tk.StringVar(value="Select a class offering.")
        ttk.Label(info_frame, textvariable=self.info_var, justify="left").pack(anchor="w")

        roster_frame = ttk.LabelFrame(frame, text="Enrolled Students", padding=10)
        roster_frame.pack(fill="both", expand=True)

        table = ttk.Frame(roster_frame)
        table.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table,
            columns=("enrollment", "student", "program", "status", "grade"),
            show="headings",
            selectmode="browse"
        )

        for key, title, width in [
            ("enrollment", "Enrollment", 110),
            ("student", "Student", 220),
            ("program", "Program", 130),
            ("status", "Status", 120),
            ("grade", "Final Grade", 140)
        ]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")

        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.summary_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.summary_var,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))

    def refresh_offerings(self):
        try:
            self.offerings = self.academic_service.get_offerings()
            self.offering_combo["values"] = [
                f"{row[0]} | {row[11]} - {row[12]} | {row[3]} | {row[5]} | {row[8]} {row[9]}"
                for row in self.offerings
            ]

            if self.offerings:
                self.offering_combo.current(0)
                self.load_roster(self.offerings[0])
            else:
                self.offering_combo.set("")
                self.clear_roster("No class offerings found.")
        except Exception as error:
            messagebox.showerror("Class View Error", str(error), parent=self)

    def on_offering_selected(self, event=None):
        index = self.offering_combo.current()
        if index >= 0:
            self.load_roster(self.offerings[index])

    def load_roster(self, offering):
        try:
            self.roster = self.enrollment_service.get_by_offering(offering[0])
            teacher = f"{offering[8]} {offering[9]}"
            subject = f"{offering[11]} - {offering[12]}"

            self.info_var.set(
                f"Offering: {offering[0]}    Class: {offering[1]}    Subject: {subject}\n"
                f"Section: {offering[3]}    Schedule: {offering[2]}    Room: {offering[6] or '-'}\n"
                f"Teacher: {teacher}    School Year: {offering[4]}    Semester: {offering[5]}"
            )

            self.tree.delete(*self.tree.get_children())
            graded_count = 0

            for enrollment in self.roster:
                saved_grade = self.grading_service.get_saved_grade(enrollment[0])

                if saved_grade:
                    grade_text = f"{float(saved_grade[1]):.2f}%"
                    graded_count += 1
                else:
                    try:
                        grade = self.grading_service.calculate_grade(enrollment[0])
                        grade_text = f"{grade:.2f}% (Calculated)"
                        graded_count += 1
                    except ValueError:
                        grade_text = "No grade yet"

                self.tree.insert("", "end", values=(
                    enrollment[0],
                    f"{enrollment[2]} {enrollment[3]}",
                    enrollment[4],
                    enrollment[5],
                    grade_text
                ))

            self.summary_var.set(
                f"Students Enrolled: {len(self.roster)}    Grades Available: {graded_count}"
            )
        except Exception as error:
            messagebox.showerror("Roster Error", str(error), parent=self)

    def clear_roster(self, message):
        self.tree.delete(*self.tree.get_children())
        self.info_var.set(message)
        self.summary_var.set("")
