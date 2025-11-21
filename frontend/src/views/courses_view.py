import customtkinter as ctk
from tkinter import messagebox
from src.api.client import api

class CoursesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.build_ui()
        self.load_courses()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="Course Catalog", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(side="left")
        
        ctk.CTkButton(header, text="+ Add Course", font=self.FONT_NORMAL,
                     height=36, fg_color="#0EA5E9", hover_color="#0284C7",
                     command=self.create_course_dialog).pack(side="right")
        
        # Course list container
        self.courses_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.courses_container.pack(fill="both", expand=True)
        
        # Table header
        header_frame = ctk.CTkFrame(self.courses_container, fg_color="#F1F5F9", corner_radius=0)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        cols = [("Code", 0.2), ("Course Name", 0.5), ("Credits", 0.15), ("Actions", 0.15)]
        for col, weight in cols:
            ctk.CTkLabel(header_frame, text=col, font=("Ubuntu", 13, "bold"),
                        text_color="#475569", anchor="w").pack(side="left", expand=True,
                                                               fill="x", padx=15, pady=10)
        
        # Scrollable content
        self.content_frame = ctk.CTkScrollableFrame(self.courses_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_courses(self):
        """Load danh sách môn học"""
        for w in self.content_frame.winfo_children():
            w.destroy()
        
        courses = api.get_all_courses()
        
        if not courses:
            ctk.CTkLabel(self.content_frame, text="No courses available",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=40)
            return
        
        for course in courses:
            self.create_course_row(course)

    def create_course_row(self, course):
        """Tạo row cho mỗi môn học"""
        row = ctk.CTkFrame(self.content_frame, fg_color="#F8FAFC", corner_radius=8,
                          border_width=1, border_color="#E2E8F0")
        row.pack(fill="x", pady=5)
        
        # Code
        ctk.CTkLabel(row, text=course['code'], font=("Ubuntu", 12, "bold"),
                    text_color="#0EA5E9", anchor="w").pack(side="left", expand=True,
                                                           fill="x", padx=15, pady=15)
        
        # Name
        ctk.CTkLabel(row, text=course['name'], font=self.FONT_NORMAL,
                    text_color="#334155", anchor="w").pack(side="left", expand=True,
                                                           fill="x", padx=15, pady=15)
        
        # Credits
        ctk.CTkLabel(row, text=f"{course['credits']} credits", font=self.FONT_SMALL,
                    text_color="#64748B", anchor="w").pack(side="left", expand=True,
                                                           fill="x", padx=15, pady=15)
        
        # Actions (placeholder for future)
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.pack(side="left", padx=15)
        
        ctk.CTkLabel(action_frame, text="—", font=self.FONT_SMALL,
                    text_color="#CBD5E1").pack()

    def create_course_dialog(self):
        """Dialog tạo môn học mới"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Course")
        dialog.geometry("450x350")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Add New Course", font=self.FONT_TITLE).pack(pady=20)
        
        # Course Code
        ctk.CTkLabel(dialog, text="Course Code:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        code_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., IT3080", font=self.FONT_NORMAL)
        code_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Course Name
        ctk.CTkLabel(dialog, text="Course Name:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., Python Programming", font=self.FONT_NORMAL)
        name_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Credits
        ctk.CTkLabel(dialog, text="Credits:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        credits_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., 3", font=self.FONT_NORMAL)
        credits_entry.pack(fill="x", padx=30, pady=(5, 20))
        
        def submit():
            code = code_entry.get().strip().upper()
            name = name_entry.get().strip()
            credits_str = credits_entry.get().strip()
            
            if not code or not name or not credits_str:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                credits = int(credits_str)
                if credits < 1 or credits > 6:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Credits must be between 1 and 6")
                return
            
            success, _ = api.create_course(code, name, credits)
            if success:
                messagebox.showinfo("Success", "Course created successfully")
                dialog.destroy()
                self.load_courses()
            else:
                messagebox.showerror("Error", "Failed to create course (code may already exist)")
        
        ctk.CTkButton(dialog, text="Create Course", font=self.FONT_NORMAL, height=40,
                     fg_color="#0EA5E9", command=submit).pack(fill="x", padx=30, pady=10)
