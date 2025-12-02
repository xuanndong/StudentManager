import customtkinter as ctk
from src.api.client import api

class StudentClassesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Header
        ctk.CTkLabel(self, text="Lớp học của tôi", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(anchor="w", pady=(0, 20))
        
        # Administrative Class
        admin_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        admin_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(admin_frame, text="Lớp chính quy", font=("Ubuntu", 16, "bold"),
                    text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        self.admin_content = ctk.CTkFrame(admin_frame, fg_color="transparent")
        self.admin_content.pack(fill="x", padx=20, pady=(0, 20))
        
        # Course Classes
        course_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        course_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(course_frame, text="Lớp học phần đã đăng ký", font=("Ubuntu", 16, "bold"),
                    text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        self.course_content = ctk.CTkScrollableFrame(course_frame, fg_color="transparent")
        self.course_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def view_admin_class_students(self, class_data):
        """Hiển thị danh sách sinh viên lớp chính quy (bạn cùng lớp)"""
        class_id = class_data.get('id', class_data.get('_id'))
        
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Bạn cùng lớp")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        # Header
        class_name = class_data.get('name', 'Class')
        academic_year = class_data.get('academic_year', 'N/A')
        
        header = ctk.CTkFrame(dialog, fg_color="#EFF6FF", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text=f"{class_name}",
                    font=("Ubuntu", 16, "bold"), text_color="#1E40AF").pack(padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text=f"Niên khóa: {academic_year}",
                    font=self.FONT_NORMAL, text_color="#3B82F6").pack(padx=20, pady=(0, 15))
        
        # Loading
        loading = ctk.CTkLabel(dialog, text="Đang tải danh sách...", text_color="#94A3B8")
        loading.pack(pady=20)
        
        # Get students
        students = api.get_administrative_class_students(class_id)
        loading.destroy()
        
        if not students:
            ctk.CTkLabel(dialog, text="Không có sinh viên trong lớp",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=30)
            return
        
        # Student count
        count_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        count_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(count_frame, text=f"Tổng: {len(students)} sinh viên",
                    font=self.FONT_NORMAL, text_color="#64748B").pack(anchor="w")
        
        # Student list
        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        # Highlight current user
        current_user_id = api.user_info.get("_id")
        
        for idx, student in enumerate(students, 1):
            is_me = student.get('_id') == current_user_id
            
            # Create frame with conditional border
            if is_me:
                item = ctk.CTkFrame(list_frame, 
                                   fg_color="#DBEAFE", 
                                   corner_radius=8,
                                   border_width=2,
                                   border_color="#3B82F6")
            else:
                item = ctk.CTkFrame(list_frame, 
                                   fg_color="#F8FAFC", 
                                   corner_radius=8)
            item.pack(fill="x", pady=3)
            
            # Number
            ctk.CTkLabel(item, text=f"{idx}.", font=self.FONT_NORMAL,
                        text_color="#1E40AF" if is_me else "#64748B", 
                        width=30).pack(side="left", padx=(10, 5))
            
            # Info
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=10)
            
            name_text = student.get('full_name', 'N/A')
            if is_me:
                name_text += " (Bạn)"
            
            ctk.CTkLabel(info, text=name_text,
                        font=("Ubuntu", 13, "bold"), 
                        text_color="#1E40AF" if is_me else "#334155").pack(anchor="w")
            ctk.CTkLabel(info, text=f"MSSV: {student.get('mssv', 'N/A')} • {student.get('email', 'N/A')}",
                        font=self.FONT_SMALL, 
                        text_color="#3B82F6" if is_me else "#64748B").pack(anchor="w")
    
    def view_students(self, class_data):
        """Hiển thị danh sách sinh viên trong lớp học phần"""
        class_id = class_data.get('id', class_data.get('_id'))
        
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Sinh viên trong lớp")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        # Header
        course_name = class_data.get('course_name', class_data.get('class_code', 'Class'))
        semester = class_data.get('semester', 'N/A')
        
        header = ctk.CTkFrame(dialog, fg_color="#F8FAFC", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text=f"{course_name} - {semester}",
                    font=("Ubuntu", 16, "bold"), text_color="#1E293B").pack(padx=20, pady=15)
        
        # Loading
        loading = ctk.CTkLabel(dialog, text="Đang tải danh sách...", text_color="#94A3B8")
        loading.pack(pady=20)
        
        # Get students
        students = api.get_course_class_students(class_id)
        loading.destroy()
        
        if not students:
            ctk.CTkLabel(dialog, text="Chưa có sinh viên đăng ký lớp này",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=30)
            return
        
        # Student count
        count_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        count_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(count_frame, text=f"Tổng: {len(students)} sinh viên",
                    font=self.FONT_NORMAL, text_color="#64748B").pack(anchor="w")
        
        # Student list
        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        for idx, student in enumerate(students, 1):
            item = ctk.CTkFrame(list_frame, fg_color="#F8FAFC", corner_radius=8)
            item.pack(fill="x", pady=3)
            
            # Number
            ctk.CTkLabel(item, text=f"{idx}.", font=self.FONT_NORMAL,
                        text_color="#64748B", width=30).pack(side="left", padx=(10, 5))
            
            # Info
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=10)
            
            ctk.CTkLabel(info, text=student.get('full_name', 'N/A'),
                        font=("Ubuntu", 13, "bold"), text_color="#334155").pack(anchor="w")
            ctk.CTkLabel(info, text=f"MSSV: {student.get('mssv', 'N/A')} • {student.get('email', 'N/A')}",
                        font=self.FONT_SMALL, text_color="#64748B").pack(anchor="w")
    
    def load_data(self):
        """Load thông tin lớp"""
        # Load administrative class
        admin_classes = api.get_my_administrative_classes()
        
        for w in self.admin_content.winfo_children():
            w.destroy()
        
        if admin_classes:
            cls = admin_classes[0]
            card = ctk.CTkFrame(self.admin_content, fg_color="#EFF6FF", corner_radius=8,
                               border_width=1, border_color="#BFDBFE")
            card.pack(fill="x")
            
            # Info section
            info_section = ctk.CTkFrame(card, fg_color="transparent")
            info_section.pack(fill="x", padx=20, pady=15)
            
            ctk.CTkLabel(info_section, text=cls['name'], font=("Ubuntu", 16, "bold"),
                        text_color="#1E40AF").pack(anchor="w")
            ctk.CTkLabel(info_section, text=f"Niên khóa: {cls.get('academic_year', 'N/A')}",
                        font=self.FONT_NORMAL, text_color="#3B82F6").pack(anchor="w")
            
            # Button section
            btn_section = ctk.CTkFrame(card, fg_color="transparent")
            btn_section.pack(fill="x", padx=20, pady=(0, 15))
            
            ctk.CTkButton(btn_section, text="Xem bạn cùng lớp", width=140, height=32,
                         fg_color="#3B82F6", hover_color="#2563EB",
                         font=self.FONT_NORMAL,
                         command=lambda c=cls: self.view_admin_class_students(c)).pack(side="right")
        else:
            ctk.CTkLabel(self.admin_content, text="Chưa được phân vào lớp chính quy",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=10)
        
        # Load course classes
        course_classes = api.get_my_course_classes()
        
        for w in self.course_content.winfo_children():
            w.destroy()
        
        if not course_classes:
            ctk.CTkLabel(self.course_content, text="Chưa đăng ký lớp học phần nào",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
            return
        
        for cls in course_classes:
            card = ctk.CTkFrame(self.course_content, fg_color="#F8FAFC", corner_radius=8,
                               border_width=1, border_color="#E2E8F0")
            card.pack(fill="x", pady=5)
            
            # Display: "Course Name - Semester" hoặc "Class Code - Semester"
            course_name = cls.get('course_name', cls.get('class_code', 'Unknown'))
            semester = cls.get('semester', 'N/A')
            display_text = f"{course_name} - {semester}"
            
            # Main info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(info_frame, text=display_text,
                        font=("Ubuntu", 14, "bold"), text_color="#334155").pack(anchor="w")
            
            # Class code and credits
            details = f"Mã lớp: {cls.get('class_code', 'N/A')}"
            if cls.get('credits'):
                details += f" • {cls.get('credits')} tín chỉ"
            ctk.CTkLabel(info_frame, text=details,
                        font=self.FONT_SMALL, text_color="#64748B").pack(anchor="w")
            
            # Button to view students
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            ctk.CTkButton(btn_frame, text="Xem sinh viên", width=120, height=28,
                         fg_color="#3B82F6", hover_color="#2563EB",
                         font=self.FONT_SMALL,
                         command=lambda c=cls: self.view_students(c)).pack(side="right")
