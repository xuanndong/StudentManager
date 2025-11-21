import customtkinter as ctk
from src.api.client import api
import threading

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 20, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.role = api.user_info.get("role", "STUDENT") if api.user_info else "STUDENT"
        self.user_name = api.user_info.get("full_name", "User") if api.user_info else "User"
        self._destroyed = False
        
        self.build_ui()
        self.add_ai_button()
        threading.Thread(target=self.load_data, daemon=True).start()

    def build_ui(self):
        # Welcome message
        welcome = ctk.CTkFrame(self, fg_color="transparent")
        welcome.pack(fill="x", pady=(0, 30))
        
        ctk.CTkLabel(welcome, text=f"Welcome back, {self.user_name}!",
                    font=self.FONT_TITLE, text_color="#1E293B").pack(anchor="w")
        
        role_text = {
            "STUDENT": "View your academic progress and class information",
            "TEACHER": "Manage your course classes and enter grades",
            "CVHT": "Monitor your students' academic performance",
            "ADMIN": "System administration and management"
        }
        ctk.CTkLabel(welcome, text=role_text.get(self.role, ""),
                    font=self.FONT_NORMAL, text_color="#64748B").pack(anchor="w", pady=(5, 0))
        
        # Loading
        self.loading = ctk.CTkLabel(self, text="Loading your dashboard...",
                                    font=self.FONT_NORMAL, text_color="#94A3B8")
        self.loading.pack(pady=50)
        
        # Content container
        self.content = ctk.CTkFrame(self, fg_color="transparent")

    def load_data(self):
        """Load dữ liệu theo role"""
        if self.role == "STUDENT":
            self.load_student_dashboard()
        elif self.role == "TEACHER":
            self.load_teacher_dashboard()
        elif self.role == "CVHT":
            self.load_cvht_dashboard()
        elif self.role == "ADMIN":
            self.load_admin_dashboard()

    def load_student_dashboard(self):
        """Dashboard cho sinh viên"""
        # Lấy tổng kết học kỳ
        summaries = api.get_my_semester_summary()
        
        # Lấy lớp chính quy
        admin_classes = api.get_my_administrative_classes()
        
        # Lấy lớp học phần
        course_classes = api.get_my_course_classes()
        
        self.after(0, lambda: self.render_student(summaries, admin_classes, course_classes))

    def render_student(self, summaries, admin_classes, course_classes):
        if self._destroyed:
            return
        try:
            self.loading.pack_forget()
            self.content.pack(fill="both", expand=True)
        except:
            return  # Widget destroyed
        
        # Row 1: Stats cards
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Tính toán stats
        total_credits = sum(s.get('credits_earned', 0) for s in summaries)
        avg_gpa = sum(s.get('gpa', 0) for s in summaries) / len(summaries) if summaries else 0
        has_warning = any(s.get('academic_warning', 0) > 0 for s in summaries)
        
        self.create_stat_card(stats_row, 0, "Overall GPA", f"{avg_gpa:.2f}",
                             "#10B981" if avg_gpa >= 3.2 else "#F59E0B" if avg_gpa >= 2.5 else "#EF4444")
        self.create_stat_card(stats_row, 1, "Total Credits", str(total_credits), "#3B82F6")
        self.create_stat_card(stats_row, 2, "Academic Status",
                             "Warning" if has_warning else "Good Standing",
                             "#EF4444" if has_warning else "#10B981")
        
        # Row 2: Administrative Class
        if admin_classes:
            cls = admin_classes[0]
            class_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12)
            class_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(class_frame, text="My Administrative Class",
                        font=("Ubuntu", 16, "bold"), text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
            
            info = ctk.CTkFrame(class_frame, fg_color="#F8FAFC", corner_radius=8)
            info.pack(fill="x", padx=20, pady=(0, 20))
            
            ctk.CTkLabel(info, text=cls['name'], font=("Ubuntu", 18, "bold"),
                        text_color="#0EA5E9").pack(padx=15, pady=(15, 5), anchor="w")
            ctk.CTkLabel(info, text=f"Academic Year: {cls.get('academic_year', 'N/A')}",
                        font=self.FONT_NORMAL, text_color="#64748B").pack(padx=15, pady=(0, 15), anchor="w")
        
        # Row 3: Enrolled Courses
        courses_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12)
        courses_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(courses_frame, text=f"Enrolled Courses ({len(course_classes)})",
                    font=("Ubuntu", 16, "bold"), text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        if not course_classes:
            ctk.CTkLabel(courses_frame, text="You are not enrolled in any courses yet",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=30)
        else:
            for cls in course_classes[:5]:  # Show max 5
                item = ctk.CTkFrame(courses_frame, fg_color="#F8FAFC", corner_radius=8)
                item.pack(fill="x", padx=20, pady=5)
                
                # Display: "Course Name - Class Code"
                course_name = cls.get('course_name', 'Unknown')
                class_code = cls.get('class_code', cls.get('semester', 'N/A'))
                display_text = f"{course_name} - {class_code}"
                
                ctk.CTkLabel(item, text=display_text,
                            font=self.FONT_NORMAL, text_color="#334155").pack(padx=15, pady=10, anchor="w")

    def load_teacher_dashboard(self):
        """Dashboard cho giáo viên"""
        course_classes = api.get_my_course_classes()
        self.after(0, lambda: self.render_teacher(course_classes))

    def render_teacher(self, course_classes):
        if self._destroyed:
            return
        try:
            self.loading.pack_forget()
            self.content.pack(fill="both", expand=True)
        except:
            return  # Widget destroyed
        
        # Stats
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)
        
        total_students = sum(len(c.get('student_ids', [])) for c in course_classes)
        
        self.create_stat_card(stats_row, 0, "My Course Classes", str(len(course_classes)), "#3B82F6")
        self.create_stat_card(stats_row, 1, "Total Students", str(total_students), "#10B981")
        self.create_stat_card(stats_row, 2, "Active Semester", "2024-1", "#8B5CF6")
        
        # Course list
        courses_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12)
        courses_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(courses_frame, text="My Course Classes",
                    font=("Ubuntu", 16, "bold"), text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        if not course_classes:
            ctk.CTkLabel(courses_frame, text="You haven't created any course classes yet",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=30)
            ctk.CTkLabel(courses_frame, text="Go to 'My Courses' to create your first class",
                        font=self.FONT_SMALL, text_color="#CBD5E1").pack()
        else:
            for cls in course_classes:
                item = ctk.CTkFrame(courses_frame, fg_color="#F8FAFC", corner_radius=8)
                item.pack(fill="x", padx=20, pady=5)
                
                left = ctk.CTkFrame(item, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
                
                # Display: "Course Name - Semester"
                course_name = cls.get('course_name', cls.get('class_code', 'Unknown'))
                semester = cls.get('semester', 'N/A')
                display_text = f"{course_name} - {semester}"
                
                ctk.CTkLabel(left, text=display_text,
                            font=("Ubuntu", 14, "bold"), text_color="#334155").pack(anchor="w")
                ctk.CTkLabel(left, text=f"{len(cls.get('student_ids', []))} students enrolled",
                            font=self.FONT_SMALL, text_color="#64748B").pack(anchor="w")

    def load_cvht_dashboard(self):
        """Dashboard cho CVHT"""
        admin_classes = api.get_my_administrative_classes()
        self.after(0, lambda: self.render_cvht(admin_classes))

    def render_cvht(self, admin_classes):
        if self._destroyed:
            return
        try:
            self.loading.pack_forget()
            self.content.pack(fill="both", expand=True)
        except:
            return  # Widget destroyed
        
        # Stats
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)
        
        total_students = sum(len(c.get('student_ids', [])) for c in admin_classes)
        
        self.create_stat_card(stats_row, 0, "My Classes", str(len(admin_classes)), "#3B82F6")
        self.create_stat_card(stats_row, 1, "Total Students", str(total_students), "#10B981")
        self.create_stat_card(stats_row, 2, "Role", "Class Advisor", "#8B5CF6")
        
        # Class list
        classes_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12)
        classes_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(classes_frame, text="My Administrative Classes",
                    font=("Ubuntu", 16, "bold"), text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        if not admin_classes:
            ctk.CTkLabel(classes_frame, text="You haven't been assigned any classes yet",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=30)
        else:
            for cls in admin_classes:
                item = ctk.CTkFrame(classes_frame, fg_color="#F8FAFC", corner_radius=8)
                item.pack(fill="x", padx=20, pady=5)
                
                left = ctk.CTkFrame(item, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
                
                ctk.CTkLabel(left, text=cls['name'],
                            font=("Ubuntu", 14, "bold"), text_color="#334155").pack(anchor="w")
                ctk.CTkLabel(left, text=f"{cls.get('academic_year', 'N/A')} • {len(cls.get('student_ids', []))} students",
                            font=self.FONT_SMALL, text_color="#64748B").pack(anchor="w")

    def load_admin_dashboard(self):
        """Dashboard cho admin"""
        users = api.get_all_users()
        courses = api.get_all_courses()
        self.after(0, lambda: self.render_admin(users, courses))

    def render_admin(self, users, courses):
        if self._destroyed:
            return
        try:
            self.loading.pack_forget()
            self.content.pack(fill="both", expand=True)
        except:
            return  # Widget destroyed
        
        # Stats
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.create_stat_card(stats_row, 0, "Total Users", str(len(users)), "#3B82F6")
        self.create_stat_card(stats_row, 1, "Total Courses", str(len(courses)), "#10B981")
        self.create_stat_card(stats_row, 2, "System", "Active", "#10B981")
        
        # Quick info
        info_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12)
        info_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(info_frame, text="System Overview",
                    font=("Ubuntu", 16, "bold"), text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        # Count by role
        role_counts = {}
        for u in users:
            role = u.get('role', 'STUDENT')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        for role, count in role_counts.items():
            item = ctk.CTkFrame(info_frame, fg_color="#F8FAFC", corner_radius=8)
            item.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(item, text=f"{role}: {count} users",
                        font=self.FONT_NORMAL, text_color="#334155").pack(padx=15, pady=10, anchor="w")

    def create_stat_card(self, parent, col, title, value, color):
        """Tạo card thống kê"""
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12,
                           border_width=1, border_color="#E2E8F0")
        card.grid(row=0, column=col, sticky="ew", padx=10)
        
        # Color bar
        ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=0).pack(fill="x")
        
        # Content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content, text=title, font=self.FONT_SMALL,
                    text_color="#64748B").pack(anchor="w")
        ctk.CTkLabel(content, text=value, font=("Ubuntu", 28, "bold"),
                    text_color="#1E293B").pack(anchor="w", pady=(5, 0))
    
    def destroy(self):
        self._destroyed = True
        super().destroy()

    
    def add_ai_button(self):
        """Add floating AI assistant button"""
        # Only for STUDENT, TEACHER, CVHT (not ADMIN)
        if self.role == "ADMIN":
            return
        
        # Floating button at bottom right
        ai_btn = ctk.CTkButton(
            self.master,
            text="AI Assistant",
            font=(self.FONT_NORMAL[0], 13, "bold"),
            fg_color="#6366F1",
            hover_color="#5558E3",
            width=150,
            height=50,
            corner_radius=25,
            command=self.open_ai_chat
        )
        # Place at bottom right corner
        ai_btn.place(relx=0.95, rely=0.95, anchor="se")
    
    def open_ai_chat(self):
        """Open AI chatbot window"""
        from src.components.ai_chatbot import AIChatbot
        
        # Check if AI is available
        health = api.check_ai_health()
        if not health.get('available'):
            from tkinter import messagebox
            messagebox.showwarning(
                "AI Not Available",
                "AI Assistant is not configured.\n\nPlease contact administrator to enable this feature."
            )
            return
        
        # Open chatbot window
        AIChatbot(self)
