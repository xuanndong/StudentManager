import customtkinter as ctk
from src.api.client import api
from PIL import Image
import os

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, on_logout):
        super().__init__(master, width=280, corner_radius=0)
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.configure(fg_color="white")
        
        # Viền phải
        ctk.CTkFrame(self, width=1, fg_color="#E5E7EB").place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        self.FONT_BOLD = ("DejaVu Sans", 16, "bold")
        self.FONT_REG = ("DejaVu Sans", 14)

        # 1. Logo
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.pack(fill="x", padx=25, pady=(30, 20))
        ctk.CTkLabel(self.logo_frame, text="nasSign", font=("DejaVu Sans", 30, "bold"), text_color="#0EA5E9").pack(anchor="w")
        ctk.CTkLabel(self.logo_frame, text="Student Manager", font=("DejaVu Sans", 12), text_color="#64748B").pack(anchor="w")

        # 2. Info Card
        self.user_info = api.user_info or {}
        self.create_user_card()

        # 3. Menu
        self.menu_btns = {}
        self.icon_path = os.path.join(os.path.dirname(__file__), "../../assets/icons")
        self.create_menus()

        # Spacer & Logout
        ctk.CTkLabel(self, text="").pack(expand=True)
        ctk.CTkButton(self, text="Log out", fg_color="#FEF2F2", text_color="#DC2626", hover_color="#FEE2E2",
                      height=45, corner_radius=10, font=self.FONT_BOLD, border_width=1, border_color="#FECACA",
                      command=self.on_logout).pack(fill="x", padx=20, pady=30)

    def create_user_card(self):
        card = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color="#E2E8F0")
        card.pack(fill="x", padx=15, pady=(0, 20))
        
        name = self.user_info.get("full_name", "Unknown")
        role = self.user_info.get("role", "STUDENT").upper()
        
        # Avatar
        av_frame = ctk.CTkFrame(card, fg_color="transparent")
        av_frame.pack(side="left", padx=10, pady=10)
        av_circle = ctk.CTkFrame(av_frame, width=45, height=45, corner_radius=22, fg_color="#E0F2FE")
        av_circle.pack()
        initial = name[0].upper() if name else "U"
        ctk.CTkLabel(av_circle, text=initial, font=("DejaVu Sans", 20, "bold"), text_color="#0284C7").place(relx=0.5, rely=0.5, anchor="center")

        # Text
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="x", pady=10)
        ctk.CTkLabel(info, text=name, font=self.FONT_BOLD, text_color="#334155", anchor="w").pack(fill="x")
        role_color = "#D97706" if role == "CVHT" else ("#DC2626" if role == "ADMIN" else "#64748B")
        ctk.CTkLabel(info, text=role, font=("DejaVu Sans", 11, "bold"), text_color=role_color, anchor="w").pack(fill="x")

    def create_menus(self):
        role = self.user_info.get("role", "STUDENT")
        
        menus = [("Dashboard", "dashboard", "dashboard.png")]
        
        if role == "ADMIN":
            menus.extend([
                ("User Manager", "users", "users.png"),
                ("Class Manager", "classes", "class.png"), # Admin view all
                ("Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])
        elif role == "CVHT":
            menus.extend([
                ("My Classes", "classes", "class.png"),
                ("Grade Manager", "grades", "grade.png"),
                ("Statistics", "stats", "stats.png"),
                ("Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])
        else: # STUDENT
            menus.extend([
                ("My Classes", "classes", "class.png"),
                ("My Grades", "grades", "grade.png"),
                ("Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])
            
        for txt, key, ico in menus:
            self.add_btn(txt, key, ico)

    def add_btn(self, text, key, icon_name):
        icon = None
        try: icon = ctk.CTkImage(Image.open(os.path.join(self.icon_path, icon_name)), size=(22, 22))
        except: pass
        
        btn = ctk.CTkButton(self, text=f"  {text}", image=icon, compound="left",
                            fg_color="transparent", text_color="#64748B", hover_color="#F1F5F9",
                            anchor="w", height=50, corner_radius=8, font=self.FONT_REG,
                            command=lambda k=key: self.nav_click(k))
        btn.pack(fill="x", pady=3, padx=15)
        self.menu_btns[key] = btn

    def nav_click(self, key):
        for b in self.menu_btns.values(): b.configure(fg_color="transparent", text_color="#64748B")
        if key in self.menu_btns:
            self.menu_btns[key].configure(fg_color="#E0F2FE", text_color="#0284C7")
        self.on_navigate(key)