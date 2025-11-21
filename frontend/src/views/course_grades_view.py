import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.api.client import api

class CourseGradesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.selected_class = None
        self.build_ui()
        self.load_classes()

    def build_ui(self):
        # Header
        ctk.CTkLabel(self, text="Grade Entry", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(anchor="w", pady=(0, 20))
        
        # Instructions
        info = ctk.CTkFrame(self, fg_color="#EFF6FF", corner_radius=8, border_width=1, border_color="#BFDBFE")
        info.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(info, text="Select a course class and import grades from Excel/CSV file",
                    font=self.FONT_NORMAL, text_color="#1E40AF").pack(padx=20, pady=15)
        
        # Class selector
        selector_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        selector_frame.pack(fill="x", pady=(0, 20))
        
        inner = ctk.CTkFrame(selector_frame, fg_color="transparent")
        inner.pack(padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="Select Course Class:", font=self.FONT_NORMAL,
                    text_color="#334155").pack(side="left", padx=(0, 15))
        
        self.class_var = ctk.StringVar(value="Select a class...")
        self.class_menu = ctk.CTkOptionMenu(inner, variable=self.class_var, values=["Loading..."],
                                            font=self.FONT_NORMAL, width=300,
                                            command=self.on_class_selected)
        self.class_menu.pack(side="left", padx=(0, 15))
        
        self.import_btn = ctk.CTkButton(inner, text="Import Grades", font=self.FONT_NORMAL,
                                       height=36, fg_color="#10B981", hover_color="#059669",
                                       command=self.import_grades, state="disabled")
        self.import_btn.pack(side="left")
        
        # Grades table
        self.table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table_content = ctk.CTkScrollableFrame(self.table_frame, fg_color="transparent")
        self.table_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.table_content, text="Select a class to view grades",
                    font=self.FONT_NORMAL, text_color="#94A3B8").pack(expand=True)

    def load_classes(self):
        """Load danh sách lớp học phần"""
        classes = api.get_my_course_classes()
        
        if not classes:
            self.class_menu.configure(values=["No classes available"])
            return
        
        self.classes_data = classes
        class_names = [f"{c['semester']} - {c['group']}" for c in classes]
        self.class_menu.configure(values=class_names)
        if class_names:
            self.class_var.set(class_names[0])
            self.on_class_selected(class_names[0])

    def on_class_selected(self, selection):
        """Khi chọn lớp"""
        if not hasattr(self, 'classes_data'):
            return
        
        for cls in self.classes_data:
            if f"{cls['semester']} - {cls['group']}" == selection:
                self.selected_class = cls
                self.import_btn.configure(state="normal")
                self.load_grades(cls['id'])
                break

    def load_grades(self, class_id):
        """Load bảng điểm"""
        for w in self.table_content.winfo_children():
            w.destroy()
        
        grades = api.get_course_class_grades(class_id)
        
        if not grades:
            ctk.CTkLabel(self.table_content, text="No grades entered yet",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=40)
            return
        
        # Header
        header = ctk.CTkFrame(self.table_content, fg_color="#F1F5F9", corner_radius=0)
        header.pack(fill="x", pady=(0, 5))
        
        cols = ["Student ID", "Midterm", "Final", "Assignment", "Total"]
        for col in cols:
            ctk.CTkLabel(header, text=col, font=("Ubuntu", 12, "bold"),
                        text_color="#475569").pack(side="left", expand=True, fill="x",
                                                   padx=10, pady=10)
        
        # Rows
        for grade in grades:
            row = ctk.CTkFrame(self.table_content, fg_color="#F8FAFC", corner_radius=0)
            row.pack(fill="x", pady=2)
            
            values = [
                grade.get('student_id', 'N/A')[:8] + "...",
                f"{grade.get('midterm_score', 'N/A')}",
                f"{grade.get('final_score', 'N/A')}",
                f"{grade.get('assignment_score', 'N/A')}",
                f"{grade.get('total_score', 'N/A')}"
            ]
            
            for val in values:
                ctk.CTkLabel(row, text=val, font=self.FONT_SMALL,
                            text_color="#334155").pack(side="left", expand=True, fill="x",
                                                       padx=10, pady=10)

    def import_grades(self):
        """Import điểm từ file"""
        if not self.selected_class:
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Excel/CSV file with grades",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            success, result = api.import_course_grades(self.selected_class['id'], file_path)
            if success:
                msg = f"Imported {result.get('success_count', 0)} grades"
                if result.get('errors'):
                    msg += f"\n{len(result['errors'])} errors"
                messagebox.showinfo("Import Result", msg)
                self.load_grades(self.selected_class['id'])
            else:
                messagebox.showerror("Error", f"Import failed: {result}")
