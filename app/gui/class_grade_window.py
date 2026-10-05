import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date

from app.services.academic_service import AcademicService
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService


class ClassGradeWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.academic = AcademicService()
        self.enrollments = EnrollmentService()
        self.grading = GradingService()
        self.scores = ScoreService()

        self.offerings = []
        self.components = []
        self.roster = []
        self._build_ui()
        self.refresh_offerings()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text="Class Grade Management",
                  font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_offerings).pack(side="right")

        select = ttk.Frame(frame, padding=(0, 10, 0, 8))
        select.pack(fill="x")
        ttk.Label(select, text="Class:").pack(side="left")
        self.offering_combo = ttk.Combobox(select, state="readonly")
        self.offering_combo.pack(side="left", fill="x", expand=True, padx=6)
        self.offering_combo.bind("<<ComboboxSelected>>", self.load_components)

        ttk.Label(select, text="Component:").pack(side="left", padx=(10, 0))
        self.component_combo = ttk.Combobox(select, state="readonly", width=32)
        self.component_combo.pack(side="left", padx=6)
        self.component_combo.bind("<<ComboboxSelected>>", self.load_roster)

        self.max_var = tk.StringVar(value="Max Score: --")
        ttk.Label(select, textvariable=self.max_var).pack(side="left", padx=8)

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("enrollment", "student", "program", "status", "score", "max"),
            show="headings"
        )
        for key, title, width in [
            ("enrollment", "Enrollment", 100),
            ("student", "Student", 230),
            ("program", "Program", 120),
            ("status", "Status", 100),
            ("score", "Score", 110),
            ("max", "Max", 80)
        ]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        actions = ttk.Frame(frame, padding=(0, 8, 0, 0))
        actions.pack(fill="x")
        ttk.Button(actions, text="Enter / Update Selected Score",
                   command=self.edit_selected_score).pack(side="left")
        ttk.Button(actions, text="Refresh Scores",
                   command=self.load_roster).pack(side="left", padx=6)

        self.summary_var = tk.StringVar()
        ttk.Label(actions, textvariable=self.summary_var,
                  font=("Segoe UI", 9, "bold")).pack(side="right")

    def refresh_offerings(self):
        try:
            self.offerings = self.academic.get_offerings()
            self.offering_combo["values"] = [
                f"{r[0]} | {r[11]} - {r[12]} | {r[3]} | {r[5]}"
                for r in self.offerings
            ]
            if self.offerings:
                self.offering_combo.current(0)
                self.load_components()
            else:
                self.offerings = []
                self.component_combo.set("")
                self.tree.delete(*self.tree.get_children())
        except Exception as error:
            messagebox.showerror("Grade Management Error", str(error), parent=self)

    def load_components(self, event=None):
        index = self.offering_combo.current()
        if index < 0:
            return
        try:
            offering_id = self.offerings[index][0]
            self.components = self.academic.get_components(offering_id)
            self.component_combo["values"] = [
                f"{r[0]} | {r[1]} | {r[2]} | Max {float(r[3]):.2f}"
                for r in self.components
            ]
            if self.components:
                self.component_combo.current(0)
                self.load_roster()
            else:
                self.component_combo.set("")
                self.tree.delete(*self.tree.get_children())
                self.max_var.set("Max Score: --")
        except Exception as error:
            messagebox.showerror("Component Error", str(error), parent=self)

    def load_roster(self, event=None):
        offering_index = self.offering_combo.current()
        component_index = self.component_combo.current()
        if offering_index < 0 or component_index < 0:
            return

        try:
            offering_id = self.offerings[offering_index][0]
            component = self.components[component_index]
            component_id = component[0]
            maximum = float(component[3])
            self.max_var.set(f"Max Score: {maximum:.2f}")

            self.roster = self.enrollments.get_by_offering(offering_id)
            self.tree.delete(*self.tree.get_children())

            score_map = {
                row[4]: row for row in self.scores.get_scores(self.roster[0][0])
            } if self.roster else {}

            recorded = 0
            for enrollment in self.roster:
                student_scores = self.scores.get_scores(enrollment[0])
                score_row = next(
                    (row for row in student_scores if row[4] == component_id),
                    None
                )

                if score_row:
                    score_text = f"{float(score_row[1]):.2f}"
                    recorded += 1
                else:
                    score_text = ""

                self.tree.insert("", "end", values=(
                    enrollment[0],
                    f"{enrollment[2]} {enrollment[3]}",
                    enrollment[4],
                    enrollment[5],
                    score_text,
                    f"{maximum:.2f}"
                ))

            self.summary_var.set(
                f"Students: {len(self.roster)}    Recorded: {recorded}"
            )
        except Exception as error:
            messagebox.showerror("Roster Error", str(error), parent=self)

    def edit_selected_score(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Student", "Select a student first.", parent=self)
            return

        values = self.tree.item(selected[0], "values")
        enrollment_id = values[0]
        component_index = self.component_combo.current()
        component = self.components[component_index]
        component_id = component[0]
        maximum = float(component[3])

        current = values[4]
        dialog = tk.Toplevel(self)
        dialog.title("Enter Score")
        dialog.geometry("340x190")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        body = ttk.Frame(dialog, padding=15)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=f"Student: {values[1]}",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(body, text=f"Maximum Score: {maximum:.2f}").pack(anchor="w", pady=(3, 8))

        score_var = tk.StringVar(value=current)
        ttk.Label(body, text="Score:").pack(anchor="w")
        entry = ttk.Entry(body, textvariable=score_var)
        entry.pack(fill="x", pady=(3, 10))
        entry.focus_set()

        def save():
            try:
                score = float(score_var.get())
                self.scores.record_score(
                    score_id=f"SC-{enrollment_id}-{component_id}",
                    enrollment_id=enrollment_id,
                    component_id=component_id,
                    score=score,
                    remarks=""
                )
                dialog.destroy()
                self.load_roster()
            except Exception as error:
                messagebox.showerror("Score Error", str(error), parent=dialog)

        ttk.Button(body, text="Save Score", command=save).pack(fill="x")
        dialog.bind("<Return>", lambda event: save())
