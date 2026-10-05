import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from app.gui.academic_window import AcademicWindow
from app.gui.class_grade_window import ClassGradeWindow
from app.gui.class_roster_window import ClassRosterWindow
from app.gui.enrollment_window import EnrollmentWindow
from app.gui.student_report_window import StudentReportWindow
from app.repositories.grade_component_repository import GradeComponentRepository
from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService


BG = "#101820"
SIDEBAR = "#0B1117"
PANEL = "#18232D"
PANEL_2 = "#1E2B36"
BORDER = "#30404C"
ACCENT = "#F99E1A"
HOVER = "#FFB84D"
TEXT = "#F3F5F7"
MUTED = "#91A0AC"


class StudentGradingGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Student Information and Grading System")
        self.geometry("1180x720")
        self.minsize(980, 620)

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
        style.configure("Treeview", background=PANEL_2, fieldbackground=PANEL_2,
                        foreground=TEXT, borderwidth=0, rowheight=32,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#263642",
                        foreground=MUTED, borderwidth=0,
                        font=("Segoe UI", 8, "bold"), padding=(8, 7))
        style.map("Treeview", background=[("selected", "#62471F")],
                  foreground=[("selected", TEXT)])

    def _panel(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER,
                            border_width=1, corner_radius=12, **kw)

    def _nav(self, parent, text, command, active=False):
        return ctk.CTkButton(
            parent, text=text, command=command, anchor="w", height=38,
            corner_radius=8, fg_color=ACCENT if active else "transparent",
            hover_color=HOVER if active else PANEL, text_color=BG if active else TEXT,
            font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        shell = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        shell.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(shell, width=215, fg_color=SIDEBAR, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="OW", text_color=ACCENT,
                     font=("Segoe UI", 30, "bold")).pack(anchor="w", padx=22, pady=(24, 0))
        ctk.CTkLabel(sidebar, text="ACADEMIC COMMAND CENTER", text_color=TEXT,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(0, 30))
        ctk.CTkLabel(sidebar, text="MAIN MENU", text_color="#5F6D78",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(0, 8))

        for text, command, active in [
            ("▣   Dashboard", lambda: None, True),
            ("●   Students", self.focus_students, False),
            ("▤   Class Grades", self.open_class_grades, False),
            ("▥   Reports", self.open_student_report, False),
            ("⚙   Academic", self.open_academic_management, False),
            ("▦   Enrollments", self.open_enrollment_management, False),
        ]:
            self._nav(sidebar, text, command, active).pack(fill="x", padx=12, pady=3)

        ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(sidebar, text="SYSTEM", text_color="#5F6D78",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(0, 8))
        self._nav(sidebar, "⟳   Refresh Data", self.refresh_students).pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(sidebar, text="Student Information\nand Grading System",
                     text_color="#596772", justify="left",
                     font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=22, pady=20)

        content = ctk.CTkFrame(shell, fg_color=BG, corner_radius=0)
        content.pack(side="left", fill="both", expand=True)

        header = ctk.CTkFrame(content, fg_color="transparent", height=66)
        header.pack(fill="x", padx=28, pady=(20, 6))
        header.pack_propagate(False)
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Dashboard", text_color=TEXT,
                     font=("Segoe UI", 25, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="STUDENT OVERVIEW", text_color=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ctk.CTkButton(header, text="⟳", command=self.refresh_students,
                      width=42, height=38, corner_radius=9, fg_color=PANEL_2,
                      hover_color=ACCENT, text_color=ACCENT,
                      font=("Segoe UI", 16, "bold")).pack(side="right", pady=6)

        cards = ctk.CTkFrame(content, fg_color="transparent")
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
                         font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=15)

        workspace = ctk.CTkFrame(content, fg_color="transparent")
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
                          corner_radius=7, fg_color=PANEL_2, hover_color="#30404C",
                          font=("Segoe UI", 9, "bold")).pack(side="left", fill="x",
                                                             expand=True, padx=3)

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
            enrollment, state="readonly", height=36, corner_radius=8,
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
                          hover_color=HOVER if color == ACCENT else "#30404C",
                          text_color=BG if color == ACCENT else TEXT,
                          font=("Segoe UI", 8, "bold")).pack(side="left", fill="x",
                                                             expand=True, padx=3)

    def focus_students(self):
        items = self.student_tree.get_children()
        if items:
            item = self.student_tree.selection()[0] if self.student_tree.selection() else items[0]
            self.student_tree.selection_set(item)
            self.student_tree.focus(item)
            self.student_tree.see(item)
            self.on_student_selected()

    def open_academic_management(self): AcademicWindow(self)
    def open_enrollment_management(self): EnrollmentWindow(self)

    def open_class_grades(self):
        try: ClassGradeWindow(self)
        except Exception as e: messagebox.showerror("Grade Management Error", str(e), parent=self)

    def open_class_roster(self):
        try: ClassRosterWindow(self)
        except Exception as e: messagebox.showerror("Class View Error", str(e), parent=self)

    def open_student_report(self):
        sid = self._get_selected_student_id()
        if sid:
            try: StudentReportWindow(self, sid)
            except Exception as e: messagebox.showerror("Student Report Error", str(e), parent=self)

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
