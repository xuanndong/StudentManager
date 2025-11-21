import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.api.client import api

class AdminClassesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.selected_class = None
        self.build_ui()
        self.load_classes(auto_select_first=True)

    def build_ui(self):
        # Header với nút tạo lớp
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="Administrative Classes", font=self.FONT_TITLE, 
                    text_color="#1E293B").pack(side="left")
        
        ctk.CTkButton(header, text="+ Create Class", font=self.FONT_NORMAL,
                     height=36, fg_color="#0EA5E9", hover_color="#0284C7",
                     command=self.create_class_dialog).pack(side="right")
        
        # Container chính
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        
        # Left: Danh sách lớp
        left_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="My Classes", font=self.FONT_TITLE,
                    text_color="#334155").pack(padx=20, pady=15, anchor="w")
        
        self.class_list_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.class_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Right: Chi tiết lớp
        self.detail_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        self.detail_frame.grid(row=0, column=1, sticky="nsew")
        
        self.detail_content = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.detail_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.detail_content, text="Select a class to view details",
                    font=self.FONT_NORMAL, text_color="#94A3B8").pack(expand=True)

    def load_classes(self, auto_select_first=False):
        """Load danh sách lớp chính quy"""
        for w in self.class_list_frame.winfo_children():
            w.destroy()
        
        classes = api.get_my_administrative_classes()
        
        if not classes:
            ctk.CTkLabel(self.class_list_frame, text="No classes yet",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
            return
        
        for cls in classes:
            self.create_class_card(cls)
        
        # Auto select first class if requested
        if auto_select_first and classes:
            self.select_class(classes[0])

    def create_class_card(self, cls):
        """Tạo card cho mỗi lớp"""
        card = ctk.CTkFrame(self.class_list_frame, fg_color="#F8FAFC", corner_radius=8)
        card.pack(fill="x", pady=5)
        
        btn = ctk.CTkButton(card, text=cls['name'], font=self.FONT_NORMAL,
                           fg_color="transparent", text_color="#334155",
                           hover_color="#E0F2FE", anchor="w", height=50,
                           command=lambda: self.select_class(cls))
        btn.pack(fill="x", padx=10, pady=5)
        
        # Hiển thị số sinh viên
        count = len(cls.get('student_ids', []))
        ctk.CTkLabel(card, text=f"{count} students • {cls.get('academic_year', 'N/A')}",
                    font=self.FONT_SMALL, text_color="#64748B").pack(padx=15, pady=(0, 10), anchor="w")

    def select_class(self, cls):
        """Hiển thị chi tiết lớp"""
        self.selected_class = cls
        
        for w in self.detail_content.winfo_children():
            w.destroy()
        
        # Header
        header = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text=cls['name'], font=self.FONT_TITLE,
                    text_color="#1E293B").pack(side="left")
        
        # Actions
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        
        ctk.CTkButton(actions, text="Import Students", font=self.FONT_SMALL,
                     height=32, fg_color="#10B981", hover_color="#059669",
                     command=self.import_students).pack(side="left", padx=5)
        
        # Info - Responsive layout
        info_frame = ctk.CTkFrame(self.detail_content, fg_color="#F8FAFC", corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_grid.pack(padx=15, pady=15, fill="x")
        info_grid.grid_columnconfigure(1, weight=1)
        
        items = [
            ("Academic Year", cls.get('academic_year', 'N/A')),
            ("Total Students", len(cls.get('student_ids', []))),
            ("Class ID", cls.get('id', cls.get('_id', 'N/A'))[:8] + "...")
        ]
        
        for i, (label, value) in enumerate(items):
            ctk.CTkLabel(info_grid, text=label, font=self.FONT_SMALL,
                        text_color="#64748B", anchor="w").grid(row=i, column=0, sticky="w", pady=5, padx=(0, 15))
            ctk.CTkLabel(info_grid, text=str(value), font=self.FONT_NORMAL,
                        text_color="#334155", anchor="w", wraplength=250).grid(row=i, column=1, sticky="w", pady=5)
        
        # Student list
        ctk.CTkLabel(self.detail_content, text="Students", font=("Ubuntu", 16, "bold"),
                    text_color="#334155").pack(anchor="w", pady=(10, 10))
        
        students_frame = ctk.CTkScrollableFrame(self.detail_content, fg_color="#F8FAFC",
                                                corner_radius=8, height=300)
        students_frame.pack(fill="both", expand=True)
        
        self.load_students(students_frame, cls.get('id', cls.get('_id')))

    def load_students(self, container, class_id):
        """Load danh sách sinh viên"""
        students = api.get_administrative_class_students(class_id)
        
        if not students:
            ctk.CTkLabel(container, text="No students in this class",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
            return
        
        # Header
        header = ctk.CTkFrame(container, fg_color="#E2E8F0", corner_radius=0)
        header.pack(fill="x", padx=5, pady=5)
        
        cols = [("MSSV", 0.2), ("Full Name", 0.4), ("Email", 0.3), ("Action", 0.1)]
        for col, weight in cols:
            ctk.CTkLabel(header, text=col, font=("Ubuntu", 12, "bold"),
                        text_color="#475569").pack(side="left", expand=True, fill="x", 
                                                   padx=10, pady=8)
        
        # Rows
        for student in students:
            row = ctk.CTkFrame(container, fg_color="white", corner_radius=0,
                              border_width=0, border_color="#E2E8F0")
            row.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(row, text=student.get('mssv', 'N/A'), font=self.FONT_SMALL,
                        text_color="#334155").pack(side="left", expand=True, fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=student.get('full_name', 'N/A'), font=self.FONT_SMALL,
                        text_color="#334155").pack(side="left", expand=True, fill="x", padx=10, pady=10)
            ctk.CTkLabel(row, text=student.get('email', 'N/A'), font=self.FONT_SMALL,
                        text_color="#64748B").pack(side="left", expand=True, fill="x", padx=10, pady=10)
            
            ctk.CTkButton(row, text="Remove", font=self.FONT_SMALL, width=80,
                         height=28, fg_color="#EF4444", hover_color="#DC2626",
                         command=lambda s=student: self.remove_student(s.get('_id', s.get('id')))).pack(side="left", padx=10)

    def create_class_dialog(self):
        """Dialog tạo lớp mới"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create Administrative Class")
        dialog.geometry("450x300")
        dialog.transient(self)
        # Wait for dialog to be visible before grab_set
        dialog.update_idletasks()
        dialog.after(10, dialog.grab_set)
        
        ctk.CTkLabel(dialog, text="Create New Class", font=self.FONT_TITLE).pack(pady=20)
        
        ctk.CTkLabel(dialog, text="Class Name:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., CNTT-K17", font=self.FONT_NORMAL)
        name_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        ctk.CTkLabel(dialog, text="Academic Year:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        year_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., 2020-2024", font=self.FONT_NORMAL)
        year_entry.pack(fill="x", padx=30, pady=(5, 20))
        
        def submit():
            name = name_entry.get().strip()
            year = year_entry.get().strip()
            
            if not name or not year:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            success, result = api.create_administrative_class(name, year)
            if success:
                messagebox.showinfo("Success", "Class created successfully")
                dialog.destroy()
                # Reload and auto-select the new class
                self.load_classes(auto_select_first=True)
            else:
                messagebox.showerror("Error", "Failed to create class")
        
        ctk.CTkButton(dialog, text="Create", font=self.FONT_NORMAL, height=40,
                     fg_color="#0EA5E9", command=submit).pack(fill="x", padx=30, pady=10)

    def import_students(self):
        """Import sinh viên từ file"""
        if not self.selected_class:
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Excel/CSV file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        
        if file_path:
            success, result = api.import_administrative_students(
                self.selected_class.get('_id', self.selected_class.get('id')), file_path)
            if success:
                msg = f"Imported {result.get('added_count', 0)} students"
                if result.get('errors'):
                    msg += f"\n{len(result['errors'])} errors"
                messagebox.showinfo("Import Result", msg)
                self.select_class(self.selected_class)  # Refresh
            else:
                messagebox.showerror("Error", f"Import failed: {result}")

    def remove_student(self, student_id):
        """Xóa sinh viên khỏi lớp"""
        if not self.selected_class:
            return
        
        if messagebox.askyesno("Confirm", "Remove this student from class?"):
            class_id = self.selected_class.get('_id', self.selected_class.get('id'))
            if api.remove_administrative_student(class_id, student_id):
                messagebox.showinfo("Success", "Student removed")
                # Reload class list to update student count
                self.load_classes()
                # Reload the selected class detail with fresh data
                classes = api.get_my_administrative_classes()
                for cls in classes:
                    if cls.get('_id', cls.get('id')) == class_id:
                        self.select_class(cls)
                        break
            else:
                messagebox.showerror("Error", "Failed to remove student")
