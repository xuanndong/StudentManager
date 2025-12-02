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
        
        ctk.CTkLabel(header, text="Danh mục môn học", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(side="left")
        
        ctk.CTkButton(header, text="+ Thêm môn học", font=self.FONT_NORMAL,
                     height=36, fg_color="#0EA5E9", hover_color="#0284C7",
                     command=self.create_course_dialog).pack(side="right")
        
        # Course list container
        self.courses_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.courses_container.pack(fill="both", expand=True)
        
        # Table header
        header_frame = ctk.CTkFrame(self.courses_container, fg_color="#F1F5F9", corner_radius=0)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        cols = [("Mã môn", 0.2), ("Tên môn học", 0.5), ("Số tín chỉ", 0.15), ("Thao tác", 0.15)]
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
            ctk.CTkLabel(self.content_frame, text="Chưa có môn học nào",
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
        ctk.CTkLabel(row, text=f"{course['credits']} tín chỉ", font=self.FONT_SMALL,
                    text_color="#64748B", anchor="w").pack(side="left", expand=True,
                                                           fill="x", padx=15, pady=15)
        
        # Actions
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.pack(side="left", padx=15)
        
        # Edit button
        ctk.CTkButton(action_frame, text="Sửa", width=60, height=28,
                     fg_color="#3B82F6", hover_color="#2563EB",
                     font=self.FONT_SMALL,
                     command=lambda c=course: self.edit_course(c)).pack(side="left", padx=3)
        
        # Delete button
        ctk.CTkButton(action_frame, text="Xóa", width=60, height=28,
                     fg_color="#EF4444", hover_color="#DC2626",
                     font=self.FONT_SMALL,
                     command=lambda c=course: self.delete_course(c)).pack(side="left", padx=3)

    def create_course_dialog(self):
        """Dialog tạo môn học mới"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Thêm môn học mới")
        dialog.geometry("450x350")
        dialog.transient(self)
        # Wait for dialog to be visible before grab_set
        dialog.update_idletasks()
        dialog.after(10, dialog.grab_set)
        
        ctk.CTkLabel(dialog, text="Thêm môn học mới", font=self.FONT_TITLE).pack(pady=20)
        
        # Course Code
        ctk.CTkLabel(dialog, text="Mã môn học:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        code_entry = ctk.CTkEntry(dialog, placeholder_text="VD: IT3080", font=self.FONT_NORMAL)
        code_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Course Name
        ctk.CTkLabel(dialog, text="Tên môn học:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="VD: Lập trình Python", font=self.FONT_NORMAL)
        name_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Credits
        ctk.CTkLabel(dialog, text="Số tín chỉ:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        credits_entry = ctk.CTkEntry(dialog, placeholder_text="VD: 3", font=self.FONT_NORMAL)
        credits_entry.pack(fill="x", padx=30, pady=(5, 20))
        
        def submit():
            code = code_entry.get().strip().upper()
            name = name_entry.get().strip()
            credits_str = credits_entry.get().strip()
            
            if not code or not name or not credits_str:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin")
                return
            
            try:
                credits = int(credits_str)
                if credits < 1 or credits > 6:
                    raise ValueError()
            except:
                messagebox.showerror("Lỗi", "Số tín chỉ phải từ 1 đến 6")
                return
            
            success, _ = api.create_course(code, name, credits)
            if success:
                messagebox.showinfo("Thành công", "Tạo môn học thành công")
                dialog.destroy()
                self.load_courses()
            else:
                messagebox.showerror("Lỗi", "Tạo môn học thất bại (mã môn có thể đã tồn tại)")
        
        ctk.CTkButton(dialog, text="Tạo môn học", font=self.FONT_NORMAL, height=40,
                     fg_color="#0EA5E9", command=submit).pack(fill="x", padx=30, pady=10)

    def edit_course(self, course):
        """Dialog chỉnh sửa môn học"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Sửa môn học: {course['code']}")
        dialog.geometry("450x350")
        dialog.transient(self)
        dialog.update_idletasks()
        dialog.after(10, dialog.grab_set)
        
        ctk.CTkLabel(dialog, text="Sửa môn học", font=self.FONT_TITLE).pack(pady=20)
        
        # Course Code (readonly)
        ctk.CTkLabel(dialog, text="Mã môn học:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        code_display = ctk.CTkEntry(dialog, font=self.FONT_NORMAL, state="disabled")
        code_display.insert(0, course['code'])
        code_display.pack(fill="x", padx=30, pady=(5, 15))
        
        # Course Name
        ctk.CTkLabel(dialog, text="Tên môn học:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        name_entry = ctk.CTkEntry(dialog, font=self.FONT_NORMAL)
        name_entry.insert(0, course['name'])
        name_entry.pack(fill="x", padx=30, pady=(5, 15))
        
        # Credits
        ctk.CTkLabel(dialog, text="Số tín chỉ:", font=self.FONT_NORMAL).pack(anchor="w", padx=30)
        credits_entry = ctk.CTkEntry(dialog, font=self.FONT_NORMAL)
        credits_entry.insert(0, str(course['credits']))
        credits_entry.pack(fill="x", padx=30, pady=(5, 20))
        
        def submit():
            name = name_entry.get().strip()
            credits_str = credits_entry.get().strip()
            
            if not name or not credits_str:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin")
                return
            
            try:
                credits = int(credits_str)
                if credits < 1 or credits > 6:
                    raise ValueError()
            except:
                messagebox.showerror("Lỗi", "Số tín chỉ phải từ 1 đến 6")
                return
            
            course_id = course.get('_id', course.get('id'))
            success, _ = api.update_course(course_id, name, credits)
            if success:
                messagebox.showinfo("Thành công", "Cập nhật môn học thành công")
                dialog.destroy()
                self.load_courses()
            else:
                messagebox.showerror("Lỗi", "Cập nhật môn học thất bại")
        
        ctk.CTkButton(dialog, text="Lưu thay đổi", font=self.FONT_NORMAL, height=40,
                     fg_color="#0EA5E9", command=submit).pack(fill="x", padx=30, pady=10)
    
    def delete_course(self, course):
        """Xóa môn học"""
        confirm_msg = f"Bạn có chắc muốn xóa môn học này?\n\n"
        confirm_msg += f"Mã môn: {course['code']}\n"
        confirm_msg += f"Tên môn: {course['name']}\n\n"
        confirm_msg += "Điều này cũng sẽ xóa tất cả lớp học phần liên quan!"
        
        if messagebox.askyesno("Xác nhận xóa", confirm_msg):
            course_id = course.get('_id', course.get('id'))
            success, _ = api.delete_course(course_id)
            if success:
                messagebox.showinfo("Thành công", "Xóa môn học thành công")
                self.load_courses()
            else:
                messagebox.showerror("Lỗi", "Xóa môn học thất bại")
