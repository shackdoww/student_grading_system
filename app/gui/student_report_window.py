import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk

from app.services.enrollment_service import EnrollmentService
from app.services.grading_service import GradingService
from app.services.student_service import StudentService


BG = "#F6F4FB"
PANEL = "#FFFFFF"
PANEL_2 = "#F0ECF8"
BORDER = "#E4DEEF"
ACCENT = "#7C5CFC"
TEXT = "#28243A"
MUTED = "#827B96"
SUCCESS = "#5BCB9A"


class StudentReportWindow(ctk.CTkFrame):
    def __init__(self, parent, student_id):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.student_service = StudentService()
        self.enrollment_service = EnrollmentService()
        self.grading_service = GradingService()
        self.student_id = student_id
        self._style()
        self._build_ui()
        self.load_report()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Report.Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, borderwidth=0, rowheight=40,
                        font=("Segoe UI", 9))
        style.configure("Report.Treeview.Heading", background=PANEL_2,
                        foreground=MUTED, borderwidth=0,
                        font=("Segoe UI", 8, "bold"), padding=(10, 10))
        style.map("Report.Treeview", background=[("selected", "#E5DEFF")],
                  foreground=[("selected", TEXT)])

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=78)
        header.pack(fill="x", padx=30, pady=(22, 8))
        header.pack_propagate(False)
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left")
        ctk.CTkLabel(title, text="Student Report", text_color=TEXT,
                     font=("Segoe UI", 27, "bold")).pack(anchor="w")
        ctk.CTkLabel(title, text="ACADEMIC PERFORMANCE", text_color=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ctk.CTkButton(header, text="↻", command=self.load_report, width=44, height=40,
                      corner_radius=16, fg_color=PANEL_2, hover_color="#E1DAEF",
                      text_color=ACCENT, font=("Segoe UI", 16, "bold")).pack(side="right", pady=6)

        profile = ctk.CTkFrame(self, fg_color=PANEL, border_color=BORDER,
                              border_width=1, corner_radius=20)
        profile.pack(fill="x", padx=30, pady=(0, 14))
        left = ctk.CTkFrame(profile, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=22, pady=18)
        self.title_var = tk.StringVar(value="Student Academic Report")
        ctk.CTkLabel(left, textvariable=self.title_var, text_color=TEXT,
                     font=("Segoe UI", 17, "bold")).pack(anchor="w")
        self.student_var = tk.StringVar()
        ctk.CTkLabel(left, textvariable=self.student_var, text_color=MUTED,
                     justify="left", anchor="w", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        body = ctk.CTkFrame(self, fg_color=PANEL, border_color=BORDER,
                            border_width=1, corner_radius=20)
        body.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        ctk.CTkLabel(body, text="ENROLLMENTS & GRADES", text_color=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(16, 8))
        table_frame = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=14)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.tree = ttk.Treeview(table_frame, columns=("enrollment","subject","class","section","semester","status","grade"),
                                 show="headings", style="Report.Treeview")
        columns=[("enrollment","Enrollment",100),("subject","Subject",180),("class","Class",90),
                 ("section","Section",90),("semester","Semester",110),("status","Status",100),("grade","Final Grade",110)]
        for column, heading, width in columns:
            self.tree.heading(column,text=heading)
            self.tree.column(column,width=width,anchor="w")
        scroll=ttk.Scrollbar(table_frame,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        footer=ctk.CTkFrame(body,fg_color=PANEL_2,corner_radius=14)
        footer.pack(fill="x",padx=14,pady=(0,14))
        self.summary_var=tk.StringVar()
        ctk.CTkLabel(footer,textvariable=self.summary_var,text_color=TEXT,
                     font=("Segoe UI",10,"bold")).pack(side="left",padx=16,pady=11)

    def load_report(self):
        try:
            student=self.student_service.get(self.student_id)
            enrollments=self.enrollment_service.get_by_student(self.student_id)
            self.title_var.set(f"{student[1]} {student[2]}")
            self.student_var.set(f"{student[0]}  •  {student[4]}  •  {student[3]}  •  {student[5]}")
            self.tree.delete(*self.tree.get_children())
            graded_count=0
            grade_total=0.0
            for enrollment in enrollments:
                saved_grade=self.grading_service.get_saved_grade(enrollment[0])
                if saved_grade:
                    grade_text=f"{float(saved_grade[1]):.2f}%"
                    grade_total+=float(saved_grade[1]); graded_count+=1
                else:
                    try:
                        calculated_grade=self.grading_service.calculate_grade(enrollment[0])
                        grade_text=f"{calculated_grade:.2f}% (Calculated)"
                        grade_total+=float(calculated_grade); graded_count+=1
                    except ValueError:
                        grade_text="No grade yet"
                self.tree.insert("","end",values=(enrollment[0],f"{enrollment[11]} - {enrollment[12]}",
                    enrollment[4],enrollment[6],enrollment[8],enrollment[2],grade_text))
            if not enrollments:
                self.summary_var.set("No enrollments found.")
            elif graded_count:
                average=grade_total/graded_count
                self.summary_var.set(f"{len(enrollments)} enrollments   •   {graded_count} grades available   •   Average {average:.2f}%")
            else:
                self.summary_var.set(f"{len(enrollments)} enrollments   •   No grades available yet")
        except Exception as error:
            messagebox.showerror("Report Error",str(error),parent=self.winfo_toplevel())
