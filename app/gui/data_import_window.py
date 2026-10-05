import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

BG = "#101820"
PANEL = "#18232D"
PANEL_2 = "#1E2B36"
BORDER = "#30404C"
ACCENT = "#F99E1A"
HOVER = "#FFB84D"
TEXT = "#F3F5F7"
MUTED = "#91A0AC"


class DataImportWindow(ctk.CTkFrame):
    """Dedicated in-app data import card.

    The first supported workflow imports students. The card is intentionally
    separated from the Dashboard so additional school-wide CSV importers can
    be added here without changing the main navigation.
    """

    REQUIRED_STUDENT_COLUMNS = [
        "student_id", "first_name", "last_name", "email", "program", "status"
    ]

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=78)
        header.pack(fill="x", padx=30, pady=(22, 8))
        header.pack_propagate(False)

        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(
            title, text="Data Import", text_color=TEXT,
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            title, text="CSV DATA MANAGEMENT", text_color=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="↻", command=self.refresh_status,
            width=42, height=38, corner_radius=9,
            fg_color=PANEL_2, hover_color=ACCENT,
            text_color=ACCENT, font=("Segoe UI", 16, "bold")
        ).pack(side="right", pady=8)

        body = ctk.CTkFrame(
            self, fg_color=PANEL, border_color=BORDER,
            border_width=1, corner_radius=12
        )
        body.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        ctk.CTkLabel(
            body, text="IMPORT SCHOOL DATA",
            text_color=ACCENT, font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            body,
            text="Load CSV records into PostgreSQL with validation and a preview before anything is saved.",
            text_color=MUTED, font=("Segoe UI", 10), anchor="w", justify="left"
        ).pack(anchor="w", padx=24, pady=(0, 18))

        self._dataset_row(
            body, "Students", "student records",
            "Import Students", self.import_students
        )

        # Reserved rows make the workflow clear while the remaining import
        # types are implemented against the same PostgreSQL schema.
        for label, description in [
            ("Teachers", "teacher records"),
            ("Subjects", "subject records"),
            ("Grading Periods", "grading-period records"),
            ("Class Offerings", "class and section records"),
            ("Grade Percentages", "grading weights"),
            ("Grade Components", "quizzes, exams, activities"),
            ("Enrollments", "student-class relationships"),
            ("Component Scores", "student scores"),
            ("Final Grades", "calculated final grades"),
        ]:
            self._dataset_row(body, label, description, "Coming Soon", None, disabled=True)

        self.status_var = tk.StringVar(value="Ready to import student CSV data.")
        ctk.CTkLabel(
            body, textvariable=self.status_var, text_color=MUTED,
            font=("Segoe UI", 9), anchor="w"
        ).pack(fill="x", padx=24, pady=(12, 22))

        self.refresh_status()

    def _dataset_row(self, parent, title, description, button_text, command, disabled=False):
        row = ctk.CTkFrame(parent, fg_color=PANEL_2, corner_radius=8, height=48)
        row.pack(fill="x", padx=24, pady=3)
        row.pack_propagate(False)

        ctk.CTkLabel(
            row, text=title, text_color=TEXT,
            font=("Segoe UI", 10, "bold"), width=150, anchor="w"
        ).pack(side="left", padx=(14, 4))
        ctk.CTkLabel(
            row, text=description, text_color=MUTED,
            font=("Segoe UI", 9), anchor="w"
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row, text=button_text, command=command,
            width=145, height=32, corner_radius=7,
            fg_color=BORDER if disabled else ACCENT,
            hover_color=BORDER if disabled else HOVER,
            text_color=MUTED if disabled else BG,
            state="disabled" if disabled else "normal",
            font=("Segoe UI", 8, "bold")
        ).pack(side="right", padx=9)

    def refresh_status(self):
        try:
            count = len(self.app.student_service.get_all())
            self.status_var.set(f"Ready. PostgreSQL currently contains {count} student record(s).")
        except Exception as error:
            self.status_var.set(f"Database status unavailable: {error}")

    def import_students(self):
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Import Student CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValueError("The CSV file is empty or has no header row.")

                headers = [header.strip() for header in reader.fieldnames]
                missing = [field for field in self.REQUIRED_STUDENT_COLUMNS if field not in headers]
                if missing:
                    raise ValueError(
                        "Missing required column(s): " + ", ".join(missing)
                    )

                students = [
                    {field: (row.get(field) or "").strip()
                     for field in self.REQUIRED_STUDENT_COLUMNS}
                    for row in reader
                ]

            if not students:
                raise ValueError("The CSV contains a header but no student records.")

            errors = self.app.student_service.validate_import(students)
            self._show_preview(path, students, errors)

        except UnicodeDecodeError:
            messagebox.showerror(
                "CSV Encoding Error",
                "Save the CSV as UTF-8 and try again.",
                parent=self.winfo_toplevel()
            )
        except csv.Error as error:
            messagebox.showerror("CSV Format Error", str(error), parent=self.winfo_toplevel())
        except Exception as error:
            messagebox.showerror("Import Error", str(error), parent=self.winfo_toplevel())

    def _show_preview(self, path, students, errors):
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Data Import - Student Preview")
        dialog.geometry("950x600")
        dialog.minsize(820, 500)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="IMPORT STUDENTS",
            text_color=ACCENT, font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", padx=24, pady=(20, 2))

        ctk.CTkLabel(
            dialog, text=path, text_color=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=24, pady=(0, 10))

        summary = tk.StringVar(
            value=f"{len(students)} record(s) found. "
            + ("Fix validation errors before importing." if errors
               else "Review the records and confirm the import.")
        )
        ctk.CTkLabel(
            dialog, textvariable=summary, text_color=TEXT,
            font=("Segoe UI", 10), anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

        frame = ctk.CTkFrame(dialog, fg_color=PANEL_2, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        tree = ttk.Treeview(
            frame, columns=self.REQUIRED_STUDENT_COLUMNS,
            show="headings", height=12
        )
        widths = {
            "student_id": 80, "first_name": 110, "last_name": 110,
            "email": 210, "program": 120, "status": 90
        }
        for column in self.REQUIRED_STUDENT_COLUMNS:
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(column, width=widths[column], anchor="w")
        tree.pack(fill="both", expand=True, padx=2, pady=2)

        for student in students:
            tree.insert("", "end", values=[student[column] for column in self.REQUIRED_STUDENT_COLUMNS])

        error_box = tk.Text(
            dialog, height=4, bg=PANEL_2, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=("Segoe UI", 9)
        )
        error_box.pack(fill="x", padx=24, pady=(0, 10))
        error_box.insert("1.0", "\n".join(errors) if errors else "Validation passed.")
        error_box.configure(state="disabled")

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(0, 18))

        import_button = ctk.CTkButton(
            buttons, text="IMPORT STUDENTS", height=38,
            corner_radius=8, fg_color=ACCENT, hover_color=HOVER,
            text_color=BG, font=("Segoe UI", 9, "bold")
        )
        import_button.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            buttons, text="CANCEL", command=dialog.destroy,
            height=38, corner_radius=8, fg_color=PANEL_2,
            hover_color=BORDER, font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        if errors:
            import_button.configure(state="disabled")
        else:
            def confirm():
                try:
                    self.app.student_service.import_students(students)
                    dialog.destroy()
                    self.app.refresh_students()
                    self.refresh_status()
                    messagebox.showinfo(
                        "Import Complete",
                        f"Successfully imported {len(students)} student record(s).",
                        parent=self.winfo_toplevel()
                    )
                except Exception as error:
                    messagebox.showerror(
                        "Import Failed", str(error), parent=dialog
                    )

            import_button.configure(command=confirm)
