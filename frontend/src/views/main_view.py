import customtkinter as ctk
from src.components.sidebar import Sidebar
from src.views.dashboard_view import DashboardView
from src.views.chat_view import ChatView
from src.views.forum_view import ForumView
from src.views.users_view import UsersView
from src.views.stats_view import StatsView
from src.api.client import api

class MainView(ctk.CTkFrame):
    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout

        # Layout: Sidebar (Fixed) - Content (Expand)
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Font chuẩn
        self.FONT_TITLE = ("Ubuntu", 24, "bold")

        # Sidebar
        self.sidebar = Sidebar(self, on_navigate=self.switch_view, on_logout=self.logout_handler)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Main Content Background
        self.content = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        
        # Grid nội dung bên phải
        self.content.grid_rowconfigure(0, weight=0) # Header
        self.content.grid_rowconfigure(1, weight=1) # View Area
        self.content.grid_columnconfigure(0, weight=1)

        # Header Bar (Trắng)
        self.header = ctk.CTkFrame(self.content, height=70, fg_color="white", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        # Đường kẻ dưới header
        ctk.CTkFrame(self.header, height=1, fg_color="#E2E8F0").pack(side="bottom", fill="x")
        
        # Tiêu đề trang
        self.lbl_title = ctk.CTkLabel(self.header, text="Dashboard", 
                                      font=self.FONT_TITLE, text_color="#334155")
        self.lbl_title.pack(side="left", padx=30, pady=20)

        # View Area (Trong suốt để lộ nền xám)
        self.view_area = ctk.CTkFrame(self.content, fg_color="transparent")
        self.view_area.grid(row=1, column=0, sticky="nsew", padx=30, pady=30)

        # Init
        self.views = {}
        self.switch_view("dashboard")

    def switch_view(self, key):
        # Xóa view cũ
        for w in self.view_area.winfo_children(): w.destroy()
        
        # Map Title
        titles = {
            "dashboard": "Tổng quan",
            "users": "Quản lý người dùng",
            "courses": "Danh mục môn học",
            "admin_classes": "Lớp chính quy",
            "course_classes": "Lớp học phần",
            "course_grades": "Nhập điểm",
            "semester_summary": "Tổng kết học kỳ",
            "student_classes": "Lớp học của tôi",
            "student_grades": "Bảng điểm của tôi",
            "forum": "Diễn đàn",
            "chat": "Tin nhắn",
            "stats": "Báo cáo thống kê"
        }
        self.lbl_title.configure(text=titles.get(key, "Tổng quan"))

        # Import views khi cần
        from src.views.admin_classes_view import AdminClassesView
        from src.views.courses_view import CoursesView
        from src.views.course_classes_view import CourseClassesView
        from src.views.course_grades_view import CourseGradesView
        from src.views.semester_summary_view import SemesterSummaryView
        from src.views.student_classes_view import StudentClassesView
        from src.views.student_grades_view import StudentGradesView

        # Map View Class
        view_map = {
            "dashboard": DashboardView,
            "users": UsersView,
            "courses": CoursesView,
            "admin_classes": AdminClassesView,
            "course_classes": CourseClassesView,
            "course_grades": CourseGradesView,
            "semester_summary": SemesterSummaryView,
            "student_classes": StudentClassesView,
            "student_grades": StudentGradesView,
            "forum": ForumView,
            "chat": ChatView,
            "stats": StatsView
        }
        
        if key in view_map:
            view_map[key](self.view_area).pack(fill="both", expand=True)

    def logout_handler(self):
        api.logout()
        self.on_logout()