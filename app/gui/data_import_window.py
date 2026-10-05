import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.services.school_data_import_service import DATASETS, SchoolDataImportService


BG = "#101820"
PANEL = "#18232D"
PANEL_2 = "#1E2B36"
BORDER = "#30404C"
ACCENT = "#F99E1A"
HOVER = "#FFB84D"
TEXT = "#F3F5F7"
MUTED = "#91A0AC"


class DataImportWindow(ctk.CTkFrame):
    """Card for importing the complete relational school dataset."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.app = app
        self.import_service = SchoolDataImportService()
        self.selected_folder = None
        self.datasets = None
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=78)
        header.pack(fill="x", padx=30, pady=(22, 8))
        header.pack_propagate(False)

        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Data Import", text_color=TEXT,
                     font=("Segoe UI", 25, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="COMPLETE SCHOOL DATASET", text_color=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")

        ctk.CTkButton(
            header, text="↻", command=self.reset,
            width=42, height=38, corner_radius=9,
            fg_color=PANEL_2, hover_color=ACCENT,
            text_color=ACCENT, font=("Segoe UI", 16, "bold")
        ).pack(side="right", pady=8)

        body = ctk.CTkFrame(self, fg_color=PANEL, border_color=BORDER,
                            border_width=1, corner_radius=12)
        body.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            top, text="IMPORT SCHOOL DATA", text_color=ACCENT,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            top,
            text="Select the folder containing the 10 school_*.csv files. "
                 "All files are validated before PostgreSQL is changed.",
            text_color=MUTED, font=("Segoe UI", 10), anchor="w", justify="left"
        ).pack(anchor="w", pady=(3, 12))

        controls = ctk.CTkFrame(top, fg_color="transparent")
        controls.pack(fill="x")

        self.folder_var = tk.StringVar(value="No school dataset folder selected.")
        ctk.CTkButton(
            controls, text="SELECT DATASET FOLDER",
            command=self.select_folder, width=190, height=36,
            corner_radius=8, fg_color=ACCENT, hover_color=HOVER,
            text_color=BG, font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        ctk.CTkLabel(
            controls, textvariable=self.folder_var, text_color=MUTED,
            font=("Segoe UI", 9), anchor="w"
        ).pack(side="left", padx=14, fill="x", expand=True)

        self.rows_frame = ctk.CTkScrollableFrame(
            body, fg_color=PANEL_2, corner_radius=9
        )
        self.rows_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        self.status_var = tk.StringVar(
            value="Select the test_data folder to begin."
        )
        ctk.CTkLabel(
            body, textvariable=self.status_var, text_color=MUTED,
            font=("Segoe UI", 9), anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 8))

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(0, 20))

        self.validate_button = ctk.CTkButton(
            actions, text="VALIDATE DATA", command=self.validate_data,
            width=155, height=38, corner_radius=8,
            fg_color=PANEL_2, hover_color=BORDER, text_color=TEXT,
            font=("Segoe UI", 9, "bold"), state="disabled"
        )
        self.validate_button.pack(side="left")

        self.import_button = ctk.CTkButton(
            actions, text="IMPORT ENTIRE SCHOOL DATASET",
            command=self.import_data, width=245, height=38, corner_radius=8,
            fg_color=ACCENT, hover_color=HOVER, text_color=BG,
            font=("Segoe UI", 9, "bold"), state="disabled"
        )
        self.import_button.pack(side="right")

        self._render_rows()

    def _render_rows(self):
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.row_vars = {}

        for table, filename, _ in DATASETS:
            row = ctk.CTkFrame(self.rows_frame, fg_color=PANEL,
                               corner_radius=7, height=42)
            row.pack(fill="x", padx=6, pady=3)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=table.replace("_", " ").title(),
                text_color=TEXT, width=185, anchor="w",
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=(12, 5))

            ctk.CTkLabel(
                row, text=filename, text_color=MUTED, anchor="w",
                font=("Segoe UI", 9)
            ).pack(side="left", fill="x", expand=True)

            var = tk.StringVar(value="NOT SELECTED")
            self.row_vars[table] = var
            ctk.CTkLabel(
                row, textvariable=var, text_color=MUTED, width=115,
                anchor="e", font=("Segoe UI", 8, "bold")
            ).pack(side="right", padx=12)

    def select_folder(self):
        folder = filedialog.askdirectory(
            parent=self.winfo_toplevel(),
            title="Select folder containing school CSV files"
        )
        if not folder:
            return

        self.selected_folder = folder
        self.datasets = None
        self.folder_var.set(folder)
        self.import_button.configure(state="disabled")
        self.validate_button.configure(state="normal")
        self.status_var.set("Folder selected. Validate all 10 CSV files before importing.")

        for table, filename, _ in DATASETS:
            path = os.path.join(folder, filename)
            self.row_vars[table].set("FOUND" if os.path.isfile(path) else "MISSING")

    def validate_data(self):
        if not self.selected_folder:
            return

        try:
            self.status_var.set("Reading and validating all school datasets...")
            self.update_idletasks()

            datasets = self.import_service.read_folder(self.selected_folder)
            errors = self.import_service.validate(datasets)

            if errors:
                self.datasets = None
                self.import_button.configure(state="disabled")
                self.status_var.set(f"Validation failed: {len(errors)} issue(s).")
                self._show_validation_errors(errors)
                return

            self.datasets = datasets
            total = sum(len(rows) for rows in datasets.values())
            for table in datasets:
                self.row_vars[table].set(f"{len(datasets[table])} RECORDS")

            self.status_var.set(
                f"Validation passed. {total} records across all 10 datasets are ready."
            )
            self.import_button.configure(state="normal")
            messagebox.showinfo(
                "Validation Passed",
                f"All 10 CSV files are valid.\n\n"
                f"{total} records are ready for a single PostgreSQL transaction.",
                parent=self.winfo_toplevel()
            )
        except Exception as error:
            self.datasets = None
            self.import_button.configure(state="disabled")
            self.status_var.set("Validation failed.")
            messagebox.showerror(
                "Validation Failed", str(error), parent=self.winfo_toplevel()
            )

    def _show_validation_errors(self, errors):
        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("School Dataset Validation Errors")
        dialog.geometry("760x520")
        dialog.minsize(620, 420)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="VALIDATION ERRORS", text_color=ACCENT,
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", padx=22, pady=(20, 5))

        ctk.CTkLabel(
            dialog, text=f"{len(errors)} issue(s) found. Nothing was imported.",
            text_color=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=22, pady=(0, 10))

        box = ctk.CTkTextbox(
            dialog, fg_color=PANEL_2, text_color=TEXT,
            corner_radius=8, font=("Segoe UI", 9)
        )
        box.pack(fill="both", expand=True, padx=22, pady=(0, 14))
        box.insert("1.0", "\n".join(f"• {error}" for error in errors))
        box.configure(state="disabled")

        ctk.CTkButton(
            dialog, text="CLOSE", command=dialog.destroy,
            width=120, height=36, corner_radius=8,
            fg_color=PANEL_2, hover_color=BORDER,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right", padx=22, pady=(0, 18))

    def import_data(self):
        if not self.datasets:
            return

        total = sum(len(rows) for rows in self.datasets.values())
        confirmed = messagebox.askyesno(
            "Import Entire School Dataset",
            f"Import {total} records across all 10 tables?\n\n"
            "Existing records with the same primary key will be updated. "
            "All tables are written in foreign-key order inside ONE transaction. "
            "If anything fails, the entire import is rolled back.",
            parent=self.winfo_toplevel()
        )
        if not confirmed:
            return

        try:
            self.import_button.configure(state="disabled")
            self.validate_button.configure(state="disabled")
            self.status_var.set("Importing all 10 datasets into PostgreSQL...")
            self.update_idletasks()

            self.import_service.import_all(self.datasets)

            self.app.refresh_students()
            self._refresh_app_cards()

            self.status_var.set(
                f"Import complete. {total} records written successfully."
            )
            messagebox.showinfo(
                "Import Complete",
                f"Successfully imported the complete school dataset.\n\n"
                f"{total} records were committed across 10 tables.",
                parent=self.winfo_toplevel()
            )
        except Exception as error:
            self.status_var.set("Import failed. PostgreSQL transaction was rolled back.")
            messagebox.showerror(
                "Import Failed",
                f"No partial import was kept.\n\n{error}",
                parent=self.winfo_toplevel()
            )
        finally:
            self.validate_button.configure(
                state="normal" if self.selected_folder else "disabled"
            )

    def _refresh_app_cards(self):
        for name, card in getattr(self.app, "cards", {}).items():
            for method_name in (
                "refresh", "refresh_data", "refresh_teachers", "refresh_subjects",
                "refresh_offerings", "refresh_periods", "refresh_percentages",
                "refresh_components"
            ):
                method = getattr(card, method_name, None)
                if callable(method):
                    try:
                        method()
                    except TypeError:
                        pass

    def reset(self):
        self.selected_folder = None
        self.datasets = None
        self.folder_var.set("No school dataset folder selected.")
        self.status_var.set("Select the test_data folder to begin.")
        self.validate_button.configure(state="disabled")
        self.import_button.configure(state="disabled")
        self._render_rows()
