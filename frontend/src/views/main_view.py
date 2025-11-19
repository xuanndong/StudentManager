import customtkinter as ctk
from src.components.sidebar import Sidebar
from src.views.dashboard_view import DashboardView
from src.views.classes_view import ClassesView
from src.views.grades_view import GradesView
from src.views.chat_view import ChatView
from src.views.forum_view import ForumView
from src.api.client import api

class MainView(ctk.CTkFrame):
    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout

        # --- 1. LAYOUT CHÍNH (2 CỘT) ---
        # Cột 0: Sidebar
        # Cột 1: Nội dung chính (Header + View Area)
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Font chuẩn Linux
        self.FONT_FAMILY = "DejaVu Sans" 

        # --- 2. SIDEBAR (BÊN TRÁI) ---
        self.sidebar = Sidebar(self, on_navigate=self.switch_view, on_logout=self.logout_handler)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # --- 3. MAIN CONTAINER (BÊN PHẢI) ---
        # Chứa Header và View Area
        self.main_container = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        
        # Grid cho bên phải:
        # Row 0: Header (Chiều cao cố định)
        # Row 1: View Area (Giãn nở)
        self.main_container.grid_rowconfigure(0, weight=0) 
        self.main_container.grid_rowconfigure(1, weight=1) 
        self.main_container.grid_columnconfigure(0, weight=1)

        # --- 4. HEADER BAR (THANH TIÊU ĐỀ TRẮNG) ---
        self.header = ctk.CTkFrame(self.main_container, height=70, fg_color="white", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        # Tiêu đề trang (Sẽ thay đổi khi bấm menu)
        self.lbl_title = ctk.CTkLabel(self.header, text="Dashboard", 
                                      font=(self.FONT_FAMILY, 24, "bold"), text_color="#334155")
        self.lbl_title.pack(side="left", padx=30, pady=20)

        # --- 5. VIEW AREA (KHUNG CHỨA NỘI DUNG) ---
        self.view_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_area.grid(row=1, column=0, sticky="nsew", padx=30, pady=(20, 30))
        
        # --- 6. KHỞI TẠO MẶC ĐỊNH ---
        self.views = {}
        # Quan trọng: Phải có self.view_area trước mới gọi hàm này được
        self.switch_view("dashboard")

    def switch_view(self, view_key):
        # Xóa nội dung cũ
        for widget in self.view_area.winfo_children():
            widget.destroy()

        # Cập nhật Tiêu đề Header
        titles = {
            "dashboard": "Dashboard Overview",
            "classes": "My Classes",
            "grades": "Academic Performance",
            "chat": "Messages",
            "stats": "Statistics"
        }
        self.lbl_title.configure(text=titles.get(view_key, "Dashboard"))

        # --- LOGIC LOAD VIEW ---
        if view_key == "dashboard":
            DashboardView(self.view_area).pack(fill="both", expand=True)
            
        elif view_key == "classes":
            # Load ClassesView
            ClassesView(self.view_area).pack(fill="both", expand=True)
        elif view_key == "grades":
            # Load GradesView
            GradesView(self.view_area).pack(fill="both", expand=True)
        elif view_key == "forum":
            # Load ForumView
            ForumView(self.view_area).pack(fill="both", expand=True)
        elif view_key == "chat":
            # Load ChatView
            ChatView(self.view_area).pack(fill="both", expand=True)
        else:
            # Các màn hình chưa làm -> Hiện Placeholder
            placeholder = ctk.CTkFrame(self.view_area, fg_color="white", corner_radius=15)
            placeholder.pack(fill="both", expand=True)
            
            ctk.CTkLabel(placeholder, text=f"Coming Soon: {view_key.title()}", 
                         font=(self.FONT_FAMILY, 24), text_color="#CBD5E1").place(relx=0.5, rely=0.5, anchor="center")

    def logout_handler(self):
        api.logout()
        self.on_logout()