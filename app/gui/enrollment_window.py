import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date

from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService
from app.services.academic_service import AcademicService


class EnrollmentWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.enrollment_service = EnrollmentService()
        self.student_service = StudentService()
        self.academic_service = AcademicService()

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ttk.Frame(self, padding=(12, 12, 12, 6))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Enrollment Management",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        ttk.Button(
            header,
            text="Refresh",
            command=self.refresh
        ).pack(side="right")

        body = ttk.Frame(self, padding=(12, 6, 12, 12))
        body.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            body,
            columns=(
                "id", "student", "subject", "class", "section",
                "date", "status", "teacher"
            ),
            show="headings",
            selectmode="browse"
        )

        columns = [
            ("id", "Enrollment ID", 110),
            ("student", "Student", 170),
            ("subject", "Subject", 150),
            ("class", "Class Code", 100),
            ("section", "Section", 80),
            ("date", "Enroll Date", 105),
            ("status", "Status", 90),
            ("teacher", "Teacher", 150)
        ]

        for column, title, width in columns:
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")

        scroll = ttk.Scrollbar(
            body,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        actions = ttk.Frame(self, padding=(12, 0, 12, 12))
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Add",
            command=self.add_enrollment
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Edit",
            command=self.edit_enrollment
        ).pack(side="left", padx=6)

        ttk.Button(
            actions,
            text="Delete",
            command=self.delete_enrollment
        ).pack(side="left")

    def refresh(self):
        try:
            students = self.student_service.get_all()
            offerings = self.academic_service.get_offerings()

            self.tree.delete(*self.tree.get_children())

            self.student_map = {
                row[0]: row for row in students
            }
            self.offering_map = {
                row[0]: row for row in offerings
            }

            for student_id, student in self.student_map.items():
                enrollments = self.enrollment_service.get_by_student(student_id)

                for enrollment in enrollments:
                    offering = self.offering_map.get(enrollment[3])

                    subject = (
                        f"{enrollment[11]} - {enrollment[12]}"
                        if len(enrollment) > 12
                        else ""
                    )

                    teacher = (
                        f"{enrollment[14]} {enrollment[15]}"
                        if len(enrollment) > 15
                        else ""
                    )

                    self.tree.insert(
                        "",
                        "end",
                        iid=enrollment[0],
                        values=(
                            enrollment[0],
                            f"{student[1]} {student[2]}",
                            subject,
                            enrollment[4],
                            enrollment[6],
                            enrollment[1],
                            enrollment[2],
                            teacher
                        )
                    )

        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def _selected_id(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Enrollment Selected",
                "Select an enrollment first."
            )
            return None

        return self.tree.item(selected[0], "values")[0]

    def add_enrollment(self):
        self.open_form()

    def edit_enrollment(self):
        enrollment_id = self._selected_id()

        if not enrollment_id:
            return

        try:
            enrollment = self.enrollment_service.get(enrollment_id)
            self.open_form(enrollment)
        except Exception as error:
            messagebox.showerror("Enrollment Error", str(error))

    def delete_enrollment(self):
        enrollment_id = self._selected_id()

        if not enrollment_id:
            return

        if not messagebox.askyesno(
            "Delete Enrollment",
            f"Delete enrollment {enrollment_id}?\n\n"
            "Related scores and the saved grade may also be removed "
            "because of the database relationships."
        ):
            return

        try:
            self.enrollment_service.delete(enrollment_id)
            self.refresh()
            messagebox.showinfo(
                "Deleted",
                "Enrollment deleted successfully."
            )
        except Exception as error:
            messagebox.showerror("Delete Error", str(error))

    def open_form(self, enrollment=None):
        editing = enrollment is not None

        dialog = tk.Toplevel(self)
        dialog.title("Edit Enrollment" if editing else "Add Enrollment")
        dialog.geometry("520x430")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Enrollment ID").pack(anchor="w")
        enrollment_id = tk.StringVar(
            value=enrollment[0] if editing else ""
        )
        enrollment_entry = ttk.Entry(
            frame,
            textvariable=enrollment_id
        )
        enrollment_entry.pack(fill="x", pady=(4, 12))

        if editing:
            enrollment_entry.configure(state="disabled")

        ttk.Label(frame, text="Student").pack(anchor="w")

        students = self.student_service.get_all()
        student_map = {
            f"{row[0]} | {row[1]} {row[2]}": row[0]
            for row in students
        }

        student_combo = ttk.Combobox(
            frame,
            state="readonly",
            values=list(student_map.keys())
        )
        student_combo.pack(fill="x", pady=(4, 12))

        if editing:
            student_id = enrollment[3]
            for label, value in student_map.items():
                if value == student_id:
                    student_combo.set(label)
                    break

        ttk.Label(frame, text="Class Offering").pack(anchor="w")

        offerings = self.academic_service.get_offerings()
        offering_map = {}

        for row in offerings:
            label = (
                f"{row[0]} | {row[11]} - {row[12]} | "
                f"{row[3]} | {row[5]} | {row[8]} {row[9]}"
            )
            offering_map[label] = row[0]

        offering_combo = ttk.Combobox(
            frame,
            state="readonly",
            values=list(offering_map.keys())
        )
        offering_combo.pack(fill="x", pady=(4, 12))

        if editing:
            offering_id = enrollment[4]
            for label, value in offering_map.items():
                if value == offering_id:
                    offering_combo.set(label)
                    break

        ttk.Label(frame, text="Enrollment Date").pack(anchor="w")
        date_var = tk.StringVar(
            value=str(enrollment[1]) if editing else str(date.today())
        )
        ttk.Entry(
            frame,
            textvariable=date_var
        ).pack(fill="x", pady=(4, 12))

        ttk.Label(frame, text="Status").pack(anchor="w")
        status_var = tk.StringVar(
            value=enrollment[2] if editing else "Enrolled"
        )
        status_combo = ttk.Combobox(
            frame,
            state="readonly",
            textvariable=status_var,
            values=("Enrolled", "Dropped", "Completed", "Withdrawn")
        )
        status_combo.pack(fill="x", pady=(4, 12))

        def save():
            selected_student = student_map.get(student_combo.get())
            selected_offering = offering_map.get(offering_combo.get())

            if not enrollment_id.get().strip():
                messagebox.showwarning(
                    "Missing Enrollment ID",
                    "Enter an enrollment ID."
                )
                return

            if not selected_student:
                messagebox.showwarning(
                    "Missing Student",
                    "Select a student."
                )
                return

            if not selected_offering:
                messagebox.showwarning(
                    "Missing Class Offering",
                    "Select a class offering."
                )
                return

            if not date_var.get().strip():
                messagebox.showwarning(
                    "Missing Date",
                    "Enter an enrollment date."
                )
                return

            try:
                self.enrollment_service.save(
                    enrollment_id.get().strip(),
                    date_var.get().strip(),
                    status_var.get().strip(),
                    selected_student,
                    selected_offering
                )

                dialog.destroy()
                self.refresh()

                messagebox.showinfo(
                    "Saved",
                    "Enrollment saved successfully."
                )

            except Exception as error:
                messagebox.showerror(
                    "Save Error",
                    str(error)
                )

        ttk.Button(
            frame,
            text="Save Enrollment",
            command=save
        ).pack(fill="x", pady=(8, 0))


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    EnrollmentWindow(root)
    root.mainloop()
