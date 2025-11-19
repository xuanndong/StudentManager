import customtkinter as ctk
from src.api.client import api
from PIL import Image
import os

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, on_logout):
        super().__init__(master, width=280, corner_radius=0) # Tăng chiều rộng lên 280
        self.on_navigate = on_navigate
        self.on_logout = on_logout

        # --- CẤU HÌNH GIAO DIỆN LIGHT ---
        self.configure(fg_color="#FFFFFF") # Nền trắng tinh
        
        # Đường viền phải
        self.border_right = ctk.CTkFrame(self, width=1, fg_color="#E5E7EB")
        self.border_right.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # FONT CHUẨN LINUX (Quan trọng để không bị vỡ hạt)
        FONT_BOLD = ("DejaVu Sans", 16, "bold")
        FONT_REGULAR = ("DejaVu Sans", 14)
        FONT_SMALL = ("DejaVu Sans", 12, "bold")

        # --- 1. LOGO AREA ---
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.pack(fill="x", padx=25, pady=(35, 25))
        
        ctk.CTkLabel(self.logo_frame, text="nasSign", 
                     font=("DejaVu Sans", 32, "bold"), text_color="#0EA5E9").pack(anchor="w")
        ctk.CTkLabel(self.logo_frame, text="Student Manager", 
                     font=("DejaVu Sans", 13), text_color="#64748B").pack(anchor="w")

        # --- 2. USER PROFILE CARD (FIX LỖI MẤT TÊN) ---
        # Dùng viền nhẹ và nền xám rất nhạt
        self.user_card = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=12, 
                                      border_width=1, border_color="#E2E8F0")
        self.user_card.pack(fill="x", padx=15, pady=(0, 30))

        user_name = "Unknown"
        user_role = "STUDENT"
        if api.user_info:
            user_name = api.user_info.get("full_name", user_name)
            user_role = api.user_info.get("role", user_role).upper()

        # --- Layout Avatar (Bên trái) ---
        self.avatar_container = ctk.CTkFrame(self.user_card, fg_color="transparent")
        self.avatar_container.pack(side="left", padx=12, pady=12)

        self.avatar_circle = ctk.CTkFrame(self.avatar_container, width=48, height=48, 
                                          corner_radius=24, fg_color="#E0F2FE")
        self.avatar_circle.pack()
        # Chữ cái đầu
        first_char = user_name[0].upper() if user_name else "U"
        ctk.CTkLabel(self.avatar_circle, text=first_char, 
                     font=("DejaVu Sans", 22, "bold"), text_color="#0284C7").place(relx=0.5, rely=0.5, anchor="center")

        # --- Layout Info (Bên phải - Dùng pack để không bị chồng đè) ---
        self.info_container = ctk.CTkFrame(self.user_card, fg_color="transparent")
        self.info_container.pack(side="left", fill="x", expand=True, pady=12, padx=(0, 10))

        # Tên user (Cho phép xuống dòng nếu quá dài nhưng ở đây ta để anchor W)
        ctk.CTkLabel(self.info_container, text=user_name, 
                     font=FONT_BOLD, text_color="#1E293B",
                     anchor="w").pack(fill="x", anchor="w")
        
        # Role (Màu cam cho CVHT, Xám cho SV)
        role_color = "#D97706" if user_role == "CVHT" else "#64748B"
        ctk.CTkLabel(self.info_container, text=user_role, 
                     font=FONT_SMALL, text_color=role_color,
                     anchor="w").pack(fill="x", anchor="w", pady=(2, 0))

        # --- 3. MENU BUTTONS ---
        self.menu_buttons = {}
        menus = [
            ("Dashboard", "dashboard", "dashboard.png"),
            ("My Classes", "classes", "class.png"),
            ("Grade Board", "grades", "grade.png"),
            ("Forum", "forum", "forum.png"),
            ("Messages", "chat", "chat.png"),
        ]
        self.icon_path = os.path.join(os.path.dirname(__file__), "../../assets/icons")

        for text, key, icon_file in menus:
            self.create_menu_btn(text, key, icon_file)

        # Spacer
        ctk.CTkLabel(self, text="").pack(expand=True)

        # --- 4. LOGOUT BUTTON ---
        self.btn_logout = ctk.CTkButton(self, text="Log out",
                                      fg_color="#FEF2F2",      # Nền đỏ nhạt
                                      text_color="#DC2626",    # Chữ đỏ đậm
                                      hover_color="#FEE2E2",
                                      border_color="#FECACA",  # Viền đỏ nhạt
                                      border_width=1,
                                      height=50,               # Cao hơn chút
                                      corner_radius=12,
                                      font=FONT_BOLD,
                                      command=self.on_logout)
        self.btn_logout.pack(fill="x", padx=20, pady=30)

    def load_icon(self, filename):
        try:
            path = os.path.join(self.icon_path, filename)
            # Resize icon to 24x24
            return ctk.CTkImage(Image.open(path), size=(24, 24))
        except:
            return None

    def create_menu_btn(self, text, key, icon_file):
        icon = self.load_icon(icon_file)
        
        btn = ctk.CTkButton(self, text=f"  {text}", 
                            image=icon,
                            compound="left",
                            fg_color="transparent", 
                            text_color="#475569", # Slate 600
                            hover_color="#F1F5F9", # Slate 100
                            anchor="w",
                            height=52, # Nút to dễ bấm
                            corner_radius=10,
                            font=("DejaVu Sans", 15, "bold"), # Font đậm dễ đọc
                            command=lambda k=key: self.handle_click(k))
        
        btn.pack(fill="x", pady=4, padx=15)
        self.menu_buttons[key] = btn

    def handle_click(self, key):
        for btn in self.menu_buttons.values():
            btn.configure(fg_color="transparent", text_color="#475569")
        
        if key in self.menu_buttons:
            self.menu_buttons[key].configure(
                fg_color="#E0F2FE",  # Sky 100
                text_color="#0284C7" # Sky 600
            )
        
        self.on_navigate(key)