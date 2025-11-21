import customtkinter as ctk
from tkinter import messagebox
from src.api.client import api

class SemesterSummaryView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.selected_class = None
        self.selected_semester = None
        self.build_ui()
        self.load_classes()

    def build_ui(self):
        # Header
        ctk.CTkLabel(self, text="Semester Summary", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(anchor="w", pady=(0, 20))
        
        # Selector
        selector_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        selector_frame.pack(fill="x", pady=(0, 20))
        
        inner = ctk.CTkFrame(selector_frame, fg_color="transparent")
        inner.pack(padx=20, pady=20)
        
        # Class selector
        ctk.CTkLabel(inner, text="Class:", font=self.FONT_NORMAL).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.class_var = ctk.StringVar(value="Select...")
        self.class_menu = ctk.CTkOptionMenu(inner, variable=self.class_var, values=["Loading..."],
                                            font=self.FONT_NORMAL, width=200)
        self.class_menu.grid(row=0, column=1, padx=10, pady=5)
        
        # Semester selector
        ctk.CTkLabel(inner, text="Semester:", font=self.FONT_NORMAL).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.semester_var = ctk.StringVar(value="2024-1")
        semester_entry = ctk.CTkEntry(inner, textvariable=self.semester_var, font=self.FONT_NORMAL, width=120)
        semester_entry.grid(row=0, column=3, padx=10, pady=5)
        
        # Buttons
        ctk.CTkButton(inner, text="Calculate GPA", font=self.FONT_NORMAL, height=36,
                     fg_color="#8B5CF6", hover_color="#7C3AED",
                     command=self.calculate_gpa).grid(row=0, column=4, padx=10, pady=5)
        
        ctk.CTkButton(inner, text="View Summary", font=self.FONT_NORMAL, height=36,
                     fg_color="#0EA5E9", hover_color="#0284C7",
                     command=self.load_summary).grid(row=0, column=5, padx=10, pady=5)
        
        # Summary table
        self.table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table_content = ctk.CTkScrollableFrame(self.table_frame, fg_color="transparent")
        self.table_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.table_content, text="Select class and semester to view summary",
                    font=self.FONT_NORMAL, text_color="#94A3B8").pack(expand=True)

    def load_classes(self):
        """Load danh sách lớp chính quy"""
        classes = api.get_my_administrative_classes()
        
        if not classes:
            self.class_menu.configure(values=["No classes"])
            return
        
        self.classes_data = classes
        class_names = [c['name'] for c in classes]
        self.class_menu.configure(values=class_names)
        if class_names:
            self.class_var.set(class_names[0])

    def calculate_gpa(self):
        """Tính toán GPA cho cả lớp"""
        class_name = self.class_var.get()
        semester = self.semester_var.get().strip()
        
        if not hasattr(self, 'classes_data') or not semester:
            messagebox.showerror("Error", "Please select class and enter semester")
            return
        
        class_id = None
        for cls in self.classes_data:
            if cls['name'] == class_name:
                class_id = cls.get('id', cls.get('_id'))
                break
        
        if not class_id:
            return
        
        success, result = api.calculate_semester_summary(class_id, semester)
        if success:
            messagebox.showinfo("Success", f"Calculated GPA for {result.get('processed', 0)} students")
            self.load_summary()
        else:
            messagebox.showerror("Error", "Failed to calculate GPA")

    def load_summary(self):
        """Load tổng kết học kỳ"""
        class_name = self.class_var.get()
        semester = self.semester_var.get().strip()
        
        if not hasattr(self, 'classes_data') or not semester:
            return
        
        class_id = None
        for cls in self.classes_data:
            if cls['name'] == class_name:
                class_id = cls.get('id', cls.get('_id'))
                break
        
        if not class_id:
            return
        
        for w in self.table_content.winfo_children():
            w.destroy()
        
        summaries = api.get_class_semester_summary(class_id, semester)
        
        if not summaries:
            ctk.CTkLabel(self.table_content, text="No summary data. Please calculate GPA first.",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=40)
            return
        
        # Header
        header = ctk.CTkFrame(self.table_content, fg_color="#F1F5F9", corner_radius=0)
        header.pack(fill="x", pady=(0, 5))
        
        cols = ["Student Name", "GPA", "Credits", "Passed", "Debt", "Warning"]
        for col in cols:
            ctk.CTkLabel(header, text=col, font=("Ubuntu", 12, "bold"),
                        text_color="#475569").pack(side="left", expand=True, fill="x",
                                                   padx=10, pady=10)
        
        # Rows
        for summary in summaries:
            row = ctk.CTkFrame(self.table_content, fg_color="#F8FAFC", corner_radius=0)
            row.pack(fill="x", pady=2)
            
            gpa = summary.get('gpa', 0)
            gpa_color = "#10B981" if gpa >= 3.2 else "#F59E0B" if gpa >= 2.5 else "#EF4444"
            
            # Display student name instead of ID
            student_name = summary.get('student_name', summary.get('student_mssv', 'Unknown'))
            ctk.CTkLabel(row, text=student_name,
                        font=self.FONT_SMALL, text_color="#334155").pack(side="left", expand=True,
                                                                         fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=f"{gpa:.2f}", font=("Ubuntu", 12, "bold"),
                        text_color=gpa_color).pack(side="left", expand=True, fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=str(summary.get('credits_earned', 0)),
                        font=self.FONT_SMALL, text_color="#334155").pack(side="left", expand=True,
                                                                         fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=str(summary.get('credits_passed', 0)),
                        font=self.FONT_SMALL, text_color="#334155").pack(side="left", expand=True,
                                                                         fill="x", padx=10, pady=10)
            
            debt_text = "Yes" if summary.get('tuition_debt') else "No"
            debt_color = "#EF4444" if summary.get('tuition_debt') else "#10B981"
            ctk.CTkLabel(row, text=debt_text, font=self.FONT_SMALL,
                        text_color=debt_color).pack(side="left", expand=True, fill="x", padx=10, pady=10)
            
            warning = summary.get('academic_warning', 0)
            warning_color = "#EF4444" if warning > 0 else "#64748B"
            ctk.CTkLabel(row, text=str(warning), font=self.FONT_SMALL,
                        text_color=warning_color).pack(side="left", expand=True, fill="x", padx=10, pady=10)
