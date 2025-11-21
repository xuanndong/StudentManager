import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.api.client import api

class CourseClassesView(ctk.CTkScrollableFrame):
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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="My Course Classes", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(side="left")
        
        ctk.CTkButton(header, text="+ Create Class", font=self.FONT_NORMAL,
                     height=36, fg_color="#0EA5E9", hover_color="#0284C7",
                     command=self.create_class_dialog).pack(side="right")
        
        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        
        # Left: Class list
        left_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="My Classes", font=self.FONT_TITLE,
                    text_color="#334155").pack(padx=20, pady=15, anchor="w")
        
        self.class_list_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.class_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Right: Details
        self.detail_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        self.detail_frame.grid(row=0, column=1, sticky="nsew")
        
        self.detail_content = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.detail_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.detail_content, text="Select a class to view details",
                    font=self.FONT_NORMAL, text_color="#94A3B8").pack(expand=True)

    def load_classes(self):
        """Load danh sách lớp học phần"""
        for w in self.class_list_frame.winfo_children():
            w.destroy()
        
        classes = api.get_my_course_classes()
        
        if not classes:
            ctk.CTkLabel(self.class_list_frame, text="No classes yet",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
            return
        
        for cls in classes:
            self.create_class_card(cls)

    def create_class_card(self, cls):
        """Card cho mỗi lớp"""
        card = ctk.CTkFrame(self.class_list_frame, fg_color="#F8FAFC", corner_radius=8,
                           border_width=2, border_color="transparent")
        card.pack(fill="x", pady=5)
                
        btn = ctk.CTkButton(card, text=f"{cls.get('semester', 'N/A')} - {cls.get('group', 'N/A')}",
                           font=self.FONT_NORMAL, fg_color="transparent", text_color="#334155",
                           hover_color="#E0F2FE", anchor="w", height=50,
                           command=lambda: self.select_class(cls))
        btn.pack(fill="x", padx=10, pady=5)
        
        count = len(cls.get('student_ids', []))
        ctk.CTkLabel(card, text=f"{count} students",
                    font=self.FONT_SMALL, text_color="#64748B").pack(padx=15, pady=(0, 10), anchor="w")

    def select_class(self, cls):
        """Hiển thị chi tiết lớp"""
        self.selected_class = cls
        
        for w in self.detail_content.winfo_children():
            w.destroy()
        
        # Header
        header = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text=f"{cls['semester']} - {cls['group']}",
                    font=self.FONT_TITLE, text_color="#1E293B").pack(side="left")
        
        # Actions
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(actions, text="Import Students", font=self.FONT_SMALL,
                     height=32, fg_color="#10B981", hover_color="#059669",
                     command=self.import_students).pack(side="left", padx=5)
        
        # Info
        info_frame = ctk.CTkFrame(self.detail_content, fg_color="#F8FAFC", corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_grid.pack(padx=15, pady=15)
        
        items = [
            ("Semester", cls.get('semester', 'N/A')),
            ("Group", cls.get('group', 'N/A')),
            ("Total Students", len(cls.get('student_ids', [])))
        ]
        
        for i, (label, value) in enumerate(items):
            ctk.CTkLabel(info_grid, text=label, font=self.FONT_SMALL,
                        text_color="#64748B").grid(row=i, column=0, sticky="w", pady=5, padx=(0, 20))
            ctk.CTkLabel(info_grid, text=str(value), font=self.FONT_NORMAL,
                        text_color="#334155").grid(row=i, column=1, sticky="w", pady=5)
        
        # Student list
        ctk.CTkLabel(self.detail_content, text="Enrolled Students",
                    font=("Ubuntu", 16, "bold"), text_color="#334155").pack(anchor="w", pady=(10, 10))
        
        students_frame = ctk.CTkScrollableFrame(self.detail_content, fg_color="#F8FAFC",
                                                corner_radius=8, height=300)
        students_frame.pack(fill="both", expand=True)
        
        self.load_students(students_frame, cls['id'])

    def load_students(self, container, class_id):
        """Load danh sách sinh viên"""
        students = api.get_course_class_students(class_id)
        
        if not students:
            ctk.CTkLabel(container, text="No students enrolled",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
            return
        
        # Header
        header = ctk.CTkFrame(container, fg_color="#E2E8F0", corner_radius=0)
        header.pack(fill="x", padx=5, pady=5)
        
        cols = [("MSSV", 0.25), ("Full Name", 0.45), ("Email", 0.3)]
        for col, weight in cols:
            ctk.CTkLabel(header, text=col, font=("Ubuntu", 12, "bold"),
                        text_color="#475569").pack(side="left", expand=True, fill="x",
                                                   padx=10, pady=8)
        
        # Rows
        for student in students:
            row = ctk.CTkFrame(container, fg_color="white", corner_radius=0)
            row.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(row, text=student.get('mssv', 'N/A'), font=self.FONT_SMALL,
                        text_color="#334155").pack(side="left", expand=True, fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=student.get('full_name', 'N/A'), font=self.FONT_SMALL,
                        text_color="#334155").pack(side="left", expand=True, fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=student.get('email', 'N/A'), font=self.FONT_SMALL,
                        text_color="#64748B").pack(side="left", expand=True, fill="x", padx=10, pady=10)

    def create_class_dialog(self):
        """Dialog tạo lớp học phần"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create Course Class")
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Create Course Class", font=self.FONT_TITLE).pack(pady=20)
        
        # Get courses
        courses = api.get_all_courses()
        if not courses:
            messagebox.showerror("Error", "No courses available. Please create courses first.")
            dialog.destroy()
            return
        
        # Course selection
        ctk.CTkLabel(dialog, text="Select Course:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        course_var = ctk.StringVar(value=courses[0]['id'])
        course_menu = ctk.CTkOptionMenu(dialog, variable=course_var,
                                        values=[f"{c['code']} - {c['name']}" for c in courses],
                                        font=self.FONT_NORMAL)
        course_menu.pack(fill="x", padx=30, pady=(5, 15))
        
        # Semester
        ctk.CTkLabel(dialog, text="Semester:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        semester_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., 2024-1", font=self.FONT_NORMAL)
        semester_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Group
        ctk.CTkLabel(dialog, text="Group:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        group_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., Nhóm 1", font=self.FONT_NORMAL)
        group_entry.pack(fill="x", padx=30, pady=(5, 20))
        
        def submit():
            selected_text = course_var.get()
            course_id = None
            for c in courses:
                if f"{c['code']} - {c['name']}" == selected_text:
                    course_id = c['id']
                    break
            
            semester = semester_entry.get().strip()
            group = group_entry.get().strip()
            
            if not course_id or not semester or not group:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            success, _ = api.create_course_class(course_id, semester, group)
            if success:
                messagebox.showinfo("Success", "Course class created successfully")
                dialog.destroy()
                self.load_classes()
            else:
                messagebox.showerror("Error", "Failed to create course class")
        
        ctk.CTkButton(dialog, text="Create", font=self.FONT_NORMAL, height=40,
                     fg_color="#0EA5E9", command=submit).pack(fill="x", padx=30, pady=10)

    def import_students(self):
        """Import sinh viên"""
        if not self.selected_class:
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Excel/CSV file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            success, result = api.import_course_students(self.selected_class['id'], file_path)
            if success:
                msg = f"Imported {result.get('added_count', 0)} students"
                if result.get('errors'):
                    msg += f"\n{len(result['errors'])} errors"
                messagebox.showinfo("Import Result", msg)
                self.select_class(self.selected_class)
            else:
                messagebox.showerror("Error", f"Import failed: {result}")
