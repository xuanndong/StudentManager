import customtkinter as ctk
from src.api.client import api
from PIL import Image
import os

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, on_logout):
        super().__init__(master, width=280, corner_radius=0)
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        
        # --- CẤU HÌNH GIAO DIỆN ---
        self.configure(fg_color="#D7DADC")
        
        # Font chuẩn Linux Mint
        self.FONT_MAIN = "Ubuntu"
        
        # Bảng màu
        self.COLOR_ACTIVE_BG = "#E0F2FE"     # Xanh rất nhạt (Nền nút khi chọn)
        self.COLOR_ACTIVE_TEXT = "#0284C7"   # Xanh đậm (Chữ khi chọn)
        self.COLOR_TEXT = "#475569"          # Xám (Chữ thường)
        self.COLOR_HOVER = "#F1F5F9"         # Xám nhạt (Khi di chuột)
        self.COLOR_ACCENT = "#0EA5E9"        # Màu nhấn chính (Logo)

        # Đường viền ngăn cách bên phải
        self.border_right = ctk.CTkFrame(self, width=1, fg_color="#E2E8F0")
        self.border_right.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # --- 1. LOGO AREA ---
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        # Logo Text với điểm nhấn
        logo_label = ctk.CTkLabel(self.logo_frame, text="nasSign", 
                                font=(self.FONT_MAIN, 28, "bold"), text_color=self.COLOR_ACCENT)
        logo_label.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(self.logo_frame, text="Quản lý sinh viên", 
                              font=(self.FONT_MAIN, 12), text_color="#94A3B8")
        subtitle.pack(anchor="w", pady=(0, 0))

        # --- 2. USER PROFILE (Thẻ người dùng gọn gàng) ---
        self.build_user_profile()

        # --- 3. MENU NAVIGATION ---
        # Container chứa menu để dễ căn chỉnh
        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.menu_buttons = {} # Lưu tham chiếu các nút
        self.icon_path = os.path.join(os.path.dirname(__file__), "../../assets/icons")
        
        self.init_menus()

        # --- 4. FOOTER (Logout) ---
        self.build_logout()

    def build_user_profile(self):
        """Tạo thẻ thông tin user gọn gàng"""
        user_name = "Unknown"
        user_role = "STUDENT"
        if api.user_info:
            user_name = api.user_info.get("full_name", user_name)
            user_role = api.user_info.get("role", user_role).upper()

        # Card container
        card = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color="#F1F5F9")
        card.pack(fill="x", padx=20, pady=(0, 25))

        # Avatar (Circle)
        av_frame = ctk.CTkFrame(card, width=44, height=44, corner_radius=22, fg_color="#BAE6FD")
        av_frame.pack(side="left", padx=12, pady=12)
        av_frame.pack_propagate(False) # Giữ kích thước cố định
        
        first_char = user_name[0].upper() if user_name else "U"
        ctk.CTkLabel(av_frame, text=first_char, 
                     font=(self.FONT_MAIN, 20, "bold"), text_color="#0369A1").place(relx=0.5, rely=0.5, anchor="center")

        # Text Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(info_frame, text=user_name, anchor="w",
                     font=(self.FONT_MAIN, 14, "bold"), text_color="#334155").pack(fill="x")
        
        role_map = {"CVHT": "#D97706", "ADMIN": "#DC2626", "STUDENT": "#64748B"}
        role_color = role_map.get(user_role, "#64748B")
        
        ctk.CTkLabel(info_frame, text=user_role, anchor="w",
                     font=(self.FONT_MAIN, 11, "bold"), text_color=role_color).pack(fill="x")

    def init_menus(self):
        """Khởi tạo menu dựa trên quyền"""
        role = api.user_info.get("role", "STUDENT") if api.user_info else "STUDENT"
        
        # Danh sách menu chuẩn
        menus = [("Tổng quan", "dashboard", "dashboard.png")]
        
        if role == "ADMIN":
            menus.extend([
                ("Người dùng", "users", "group.png"),
                ("Môn học", "courses", "class.png"),
                ("Lớp chính quy", "admin_classes", "layout.png"),
            ])
        elif role == "CVHT":
            menus.extend([
                ("Lớp chủ nhiệm", "admin_classes", "class.png"),
                ("Tổng kết học kỳ", "semester_summary", "grade.png"),
                ("Thống kê", "stats", "calendar.png"),
                ("Diễn đàn", "forum", "forum.png"),
            ])
        elif role == "TEACHER":
            menus.extend([
                ("Lớp học phần", "course_classes", "class.png"),
                ("Nhập điểm", "course_grades", "grade.png"),
                ("Diễn đàn", "forum", "forum.png"),
            ])
        else: # STUDENT
            menus.extend([
                ("Lớp học của tôi", "student_classes", "class.png"),
                ("Điểm của tôi", "student_grades", "grade.png"),
                ("Diễn đàn", "forum", "forum.png"),
            ])
        
        # Messages - only for non-ADMIN
        if role != "ADMIN":
            menus.append(("Tin nhắn", "chat", "chat.png"))
        
        # Tạo nút
        for text, key, icon in menus:
            self.create_menu_btn(text, key, icon)

    def create_menu_btn(self, text, key, icon_name):
        """Tạo một nút menu đồng nhất"""
        icon_img = None
        try:
            icon_img = ctk.CTkImage(Image.open(os.path.join(self.icon_path, icon_name)), size=(22, 22))
        except: pass

        # Container cho nút
        btn = ctk.CTkButton(
            self.menu_frame, 
            text=f"  {text}", 
            image=icon_img, 
            compound="left",
            font=(self.FONT_MAIN, 14, "bold"),
            anchor="w",                 # Căn trái
            height=48,                  # Chiều cao cố định
            corner_radius=8,            # Bo góc vừa phải
            fg_color="transparent",     # Mặc định trong suốt
            text_color=self.COLOR_TEXT,
            hover_color=self.COLOR_HOVER,
            command=lambda k=key: self.handle_click(k)
        )
        btn.pack(fill="x", pady=4) # Khoảng cách giữa các nút là 4px
        
        self.menu_buttons[key] = btn

    def handle_click(self, key):
        """Xử lý hiệu ứng khi click"""
        # 1. Reset tất cả về trạng thái thường
        for btn in self.menu_buttons.values():
            btn.configure(fg_color="transparent", text_color=self.COLOR_TEXT)
        
        # 2. Highlight nút được chọn
        if key in self.menu_buttons:
            self.menu_buttons[key].configure(
                fg_color=self.COLOR_ACTIVE_BG, 
                text_color=self.COLOR_ACTIVE_TEXT
            )
        
        # 3. Chuyển trang
        self.on_navigate(key)

    def build_logout(self):
        """Nút đăng xuất tách biệt"""
        # Đường kẻ mờ phân cách
        ctk.CTkFrame(self, height=1, fg_color="#F1F5F9").pack(fill="x", padx=20, pady=(10, 10))
        
        btn = ctk.CTkButton(
            self, 
            text="Đăng xuất",
            font=(self.FONT_MAIN, 14, "bold"),
            height=45,
            corner_radius=10,
            fg_color="#FEF2F2",       # Đỏ rất nhạt
            text_color="#EF4444",     # Đỏ
            hover_color="#FEE2E2",
            border_width=0,
            command=self.on_logout
        )
        btn.pack(fill="x", padx=25, pady=(10, 30), side="bottom")