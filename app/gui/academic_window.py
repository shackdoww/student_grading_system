import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date

from app.services.academic_service import AcademicService


class AcademicWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.service = AcademicService()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_teachers_tab()
        self._build_subjects_tab()
        self._build_offerings_tab()
        self._build_periods_tab()
        self._build_percentages_tab()
        self._build_components_tab()

    def _tab(self, title):
        frame = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(frame, text=title)
        return frame

    def _tree(self, parent, columns):
        tree = ttk.Treeview(parent, columns=[c[0] for c in columns],
                            show="headings", selectmode="browse")
        for key, title, width in columns:
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _actions(self, parent, add, edit, delete, refresh):
        frame = ttk.Frame(parent, padding=(0, 10, 0, 0))
        frame.pack(fill="x")
        ttk.Button(frame, text="Add", command=add).pack(side="left")
        ttk.Button(frame, text="Edit", command=edit).pack(side="left", padx=5)
        ttk.Button(frame, text="Delete", command=delete).pack(side="left")
        ttk.Button(frame, text="Refresh", command=refresh).pack(side="right")

    def _selected(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a record first.", parent=self)
            return None
        return tree.item(selection[0], "values")

    def _form(self, title, fields, values, save_callback):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("470x520")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        variables = {}

        for label, value in zip(fields, values):
            ttk.Label(frame, text=label).pack(anchor="w", pady=(4, 2))
            var = tk.StringVar(value=str(value) if value is not None else "")
            variables[label] = var
            ttk.Entry(frame, textvariable=var).pack(fill="x", pady=(0, 5))

        def save():
            try:
                save_callback({key: var.get().strip() for key, var in variables.items()})
                dialog.destroy()
            except Exception as error:
                messagebox.showerror("Save Error", str(error), parent=dialog)

        ttk.Button(frame, text="Save", command=save).pack(fill="x", pady=15)

    def _build_teachers_tab(self):
        tab = self._tab("Teachers")
        self.teacher_tree = self._tree(tab, [
            ("id", "ID", 90), ("name", "Name", 180), ("email", "Email", 230),
            ("department", "Department", 180), ("status", "Status", 100)
        ])
        self._actions(tab, self.add_teacher, self.edit_teacher,
                       self.delete_teacher, self.refresh_teachers)
        self.refresh_teachers()

    def refresh_teachers(self):
        rows = self.service.get_teachers()
        self.teacher_tree.delete(*self.teacher_tree.get_children())
        for r in rows:
            self.teacher_tree.insert("", "end",
                                    values=(r[0], f"{r[1]} {r[2]}", r[3], r[4], r[5]))

    def add_teacher(self):
        self._teacher_form()

    def edit_teacher(self):
        r = self._selected(self.teacher_tree)
        if r:
            self._teacher_form(self.service.get_teacher(r[0]))

    def _teacher_form(self, teacher=None):
        values = teacher or ("", "", "", "", "", "Active")
        fields = ["Teacher ID", "First Name", "Last Name", "Email", "Department", "Status"]
        def save(v):
            self.service.save_teacher(v["Teacher ID"], v["First Name"], v["Last Name"],
                                      v["Email"], v["Department"], v["Status"])
            self.refresh_teachers()
        self._form("Edit Teacher" if teacher else "Add Teacher", fields, values, save)

    def delete_teacher(self):
        r = self._selected(self.teacher_tree)
        if r and messagebox.askyesno("Delete Teacher", f"Delete {r[1]} ({r[0]})?",
                                     parent=self):
            try:
                self.service.delete_teacher(r[0])
                self.refresh_teachers()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)

    def _build_subjects_tab(self):
        tab = self._tab("Subjects")
        self.subject_tree = self._tree(tab, [
            ("id", "ID", 90), ("code", "Code", 110), ("name", "Subject", 220),
            ("units", "Units", 70), ("description", "Description", 300)
        ])
        self._actions(tab, self.add_subject, self.edit_subject,
                       self.delete_subject, self.refresh_subjects)
        self.refresh_subjects()

    def refresh_subjects(self):
        rows = self.service.get_subjects()
        self.subject_tree.delete(*self.subject_tree.get_children())
        for r in rows:
            self.subject_tree.insert("", "end", values=(r[0], r[1], r[2], r[4], r[3] or ""))

    def add_subject(self):
        self._subject_form()

    def edit_subject(self):
        r = self._selected(self.subject_tree)
        if r:
            self._subject_form(self.service.get_subject(r[0]))

    def _subject_form(self, subject=None):
        values = subject or ("", "", "", "", "3")
        fields = ["Subject ID", "Subject Code", "Subject Name", "Description", "Units"]
        def save(v):
            self.service.save_subject(v["Subject ID"], v["Subject Code"], v["Subject Name"],
                                      v["Description"], v["Units"])
            self.refresh_subjects()
        self._form("Edit Subject" if subject else "Add Subject", fields, values, save)

    def delete_subject(self):
        r = self._selected(self.subject_tree)
        if r and messagebox.askyesno("Delete Subject", f"Delete {r[1]} ({r[0]})?",
                                     parent=self):
            try:
                self.service.delete_subject(r[0])
                self.refresh_subjects()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)

    def _build_offerings_tab(self):
        tab = self._tab("Class Offerings")
        self.offering_tree = self._tree(tab, [
            ("id", "ID", 80), ("code", "Class", 90), ("subject", "Subject", 170),
            ("teacher", "Teacher", 170), ("section", "Section", 90),
            ("schedule", "Schedule", 180), ("room", "Room", 90)
        ])
        self._actions(tab, self.add_offering, self.edit_offering,
                       self.delete_offering, self.refresh_offerings)
        self.refresh_offerings()

    def refresh_offerings(self):
        rows = self.service.get_offerings()
        self.offering_tree.delete(*self.offering_tree.get_children())
        for r in rows:
            self.offering_tree.insert("", "end",
                values=(r[0], r[1], f"{r[11]} - {r[12]}",
                        f"{r[8]} {r[9]}", r[3], r[2], r[6] or ""))

    def add_offering(self):
        self._offering_form()

    def edit_offering(self):
        r = self._selected(self.offering_tree)
        if r:
            offering = next((x for x in self.service.get_offerings() if x[0] == r[0]), None)
            self._offering_form(offering)

    def _offering_form(self, offering=None):
        values = offering or ("", "", "", "", "", "", "", "", "")
        fields = ["Offering ID", "Class Code", "Schedule", "Section",
                  "School Year", "Semester", "Room", "Teacher ID", "Subject ID"]
        def save(v):
            self.service.save_offering(v["Offering ID"], v["Class Code"], v["Schedule"],
                v["Section"], v["School Year"], v["Semester"], v["Room"],
                v["Teacher ID"], v["Subject ID"])
            self.refresh_offerings()
        self._form("Edit Class Offering" if offering else "Add Class Offering",
                   fields, values, save)

    def delete_offering(self):
        r = self._selected(self.offering_tree)
        if r and messagebox.askyesno("Delete Class Offering", f"Delete {r[0]}?",
                                     parent=self):
            try:
                self.service.delete_offering(r[0])
                self.refresh_offerings()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)

    def _build_periods_tab(self):
        tab = self._tab("Grading Periods")
        self.period_tree = self._tree(tab, [
            ("id", "ID", 90), ("name", "Period", 120), ("start", "Start", 110),
            ("end", "End", 110), ("year", "School Year", 110), ("semester", "Semester", 100)
        ])
        self._actions(tab, self.add_period, self.edit_period,
                       self.delete_period, self.refresh_periods)
        self.refresh_periods()

    def refresh_periods(self):
        rows = self.service.get_periods()
        self.period_tree.delete(*self.period_tree.get_children())
        for r in rows:
            self.period_tree.insert("", "end", values=r)

    def add_period(self):
        self._period_form()

    def edit_period(self):
        r = self._selected(self.period_tree)
        if r:
            self._period_form(r)

    def _period_form(self, period=None):
        values = period or ("", "", date.today(), date.today(), "", "")
        fields = ["Period ID", "Name", "Start Date", "End Date", "School Year", "Semester"]
        def save(v):
            self.service.save_period(v["Period ID"], v["Name"], v["Start Date"],
                v["End Date"], v["School Year"], v["Semester"])
            self.refresh_periods()
        self._form("Edit Grading Period" if period else "Add Grading Period",
                   fields, values, save)

    def delete_period(self):
        r = self._selected(self.period_tree)
        if r and messagebox.askyesno("Delete Grading Period", f"Delete {r[0]}?",
                                     parent=self):
            try:
                self.service.delete_period(r[0])
                self.refresh_periods()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)

    def _build_percentages_tab(self):
        tab = self._tab("Grade Percentages")
        self.percentage_tree = self._tree(tab, [
            ("id", "ID", 100), ("percentage", "Percentage", 110), ("offering", "Offering", 120)
        ])
        self._actions(tab, self.add_percentage, self.edit_percentage,
                       self.delete_percentage, self.refresh_percentages)
        self.refresh_percentages()

    def refresh_percentages(self):
        rows = []
        for offering in self.service.get_offerings():
            rows.extend(self.service.get_percentages(offering[0]))
        self.percentage_tree.delete(*self.percentage_tree.get_children())
        for r in rows:
            self.percentage_tree.insert("", "end", values=(r[0], f"{float(r[1]):.2f}%", r[2]))

    def add_percentage(self):
        self._percentage_form()

    def edit_percentage(self):
        r = self._selected(self.percentage_tree)
        if r:
            self._percentage_form(r)

    def _percentage_form(self, row=None):
        values = row or ("", "30", "")
        fields = ["Percentage ID", "Percentage", "Offering ID"]
        def save(v):
            self.service.save_percentage(v["Percentage ID"], v["Percentage"], v["Offering ID"])
            self.refresh_percentages()
        self._form("Edit Grade Percentage" if row else "Add Grade Percentage",
                   fields, values, save)

    def delete_percentage(self):
        r = self._selected(self.percentage_tree)
        if r and messagebox.askyesno("Delete Grade Percentage", f"Delete {r[0]}?",
                                     parent=self):
            try:
                self.service.delete_percentage(r[0])
                self.refresh_percentages()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)

    def _build_components_tab(self):
        tab = self._tab("Grade Components")
        self.component_tree = self._tree(tab, [
            ("id", "ID", 90), ("name", "Component", 170), ("type", "Type", 100),
            ("max", "Max Score", 90), ("period", "Period", 100),
            ("percentage", "Percentage ID", 120)
        ])
        self._actions(tab, self.add_component, self.edit_component,
                       self.delete_component, self.refresh_components)
        self.refresh_components()

    def refresh_components(self):
        rows = []
        for offering in self.service.get_offerings():
            rows.extend(self.service.get_components(offering[0]))
        self.component_tree.delete(*self.component_tree.get_children())
        for r in rows:
            self.component_tree.insert("", "end",
                values=(r[0], r[1], r[2], f"{float(r[3]):.2f}", r[6], r[7]))

    def add_component(self):
        self._component_form()

    def edit_component(self):
        r = self._selected(self.component_tree)
        if r:
            self._component_form(r)

    def _component_form(self, row=None):
        values = row or ("", "", "Quiz", "20", "", "", "")
        fields = ["Component ID", "Name", "Type", "Max Score",
                  "Description", "Period ID", "Percentage ID"]
        def save(v):
            self.service.save_component(v["Component ID"], v["Name"], v["Type"],
                v["Max Score"], v["Description"], v["Period ID"], v["Percentage ID"])
            self.refresh_components()
        self._form("Edit Grade Component" if row else "Add Grade Component",
                   fields, values, save)

    def delete_component(self):
        r = self._selected(self.component_tree)
        if r and messagebox.askyesno("Delete Grade Component", f"Delete {r[0]}?",
                                     parent=self):
            try:
                self.service.delete_component(r[0])
                self.refresh_components()
            except Exception as error:
                messagebox.showerror("Delete Error", str(error), parent=self)
