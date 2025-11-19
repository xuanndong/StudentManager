import customtkinter as ctk
from src.api.client import api
from PIL import Image
import os

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, on_logout):
        super().__init__(master, width=280, corner_radius=0)
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        
        self.configure(fg_color="#FFFFFF") # Nền trắng
        self.border_right = ctk.CTkFrame(self, width=1, fg_color="#E5E7EB")
        self.border_right.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        FONT = "DejaVu Sans"

        # LOGO
        self.logo = ctk.CTkFrame(self, fg_color="transparent")
        self.logo.pack(fill="x", padx=25, pady=(30, 20))
        ctk.CTkLabel(self.logo, text="nasSign", font=(FONT, 30, "bold"), text_color="#0EA5E9").pack(anchor="w")
        ctk.CTkLabel(self.logo, text="Student Manager", font=(FONT, 12), text_color="#64748B").pack(anchor="w")

        # USER INFO
        user_name = api.user_info.get("full_name", "Unknown") if api.user_info else "User"
        user_role = api.user_info.get("role", "STUDENT").upper() if api.user_info else "STUDENT"

        self.card = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color="#E2E8F0")
        self.card.pack(fill="x", padx=15, pady=(0, 20))
        
        # Avatar & Text (Dùng Pack để tránh lỗi đè chữ)
        av_box = ctk.CTkFrame(self.card, fg_color="transparent")
        av_box.pack(side="left", padx=10, pady=10)
        av_bg = ctk.CTkFrame(av_box, width=45, height=45, corner_radius=22, fg_color="#E0F2FE")
        av_bg.pack()
        ctk.CTkLabel(av_bg, text=user_name[0].upper(), font=(FONT, 20, "bold"), text_color="#0284C7").place(relx=0.5, rely=0.5, anchor="center")

        info_box = ctk.CTkFrame(self.card, fg_color="transparent")
        info_box.pack(side="left", fill="x", pady=10)
        ctk.CTkLabel(info_box, text=user_name, font=(FONT, 14, "bold"), text_color="#334155", anchor="w").pack(fill="x")
        role_color = "#D97706" if user_role == "CVHT" else "#64748B"
        ctk.CTkLabel(info_box, text=user_role, font=(FONT, 11, "bold"), text_color=role_color, anchor="w").pack(fill="x")

        # MENU BUTTONS (Logic Phân quyền)
        self.menu_btns = {}
        self.icon_path = os.path.join(os.path.dirname(__file__), "../../assets/icons")

        # Menu chung
        menus = [("Dashboard", "dashboard", "dashboard.png")]

        if user_role == "ADMIN":
            # ADMIN có quyền cao nhất
            menus.extend([
                ("User Management", "users", "layout.png"),
                ("All Classes", "classes", "class.png"),
                ("All Grades", "grades", "grade.png"),
                ("Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])
        elif user_role == "CVHT":
            menus.extend([
                ("Manage Classes", "classes", "class.png"),
                ("Manage Grades", "grades", "grade.png"),
                ("Statistics", "stats", "dashboard.png"),
                ("Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])
        else:  # STUDENT
            menus.extend([
                ("My Classes", "classes", "class.png"),
                ("My Grades", "grades", "grade.png"),
                ("Class Forum", "forum", "forum.png"),
                ("Messages", "chat", "chat.png"),
            ])

        for txt, key, ico in menus:
            self.add_menu_btn(txt, key, ico)

        # Spacer
        ctk.CTkLabel(self, text="").pack(expand=True)

        # Logout
        self.btn_out = ctk.CTkButton(self, text="Log out", fg_color="#FEF2F2", text_color="#DC2626",
                                     hover_color="#FEE2E2", border_color="#FECACA", border_width=1,
                                     height=45, corner_radius=10, font=(FONT, 14, "bold"),
                                     command=self.on_logout)
        self.btn_out.pack(fill="x", padx=20, pady=30)

    def add_menu_btn(self, text, key, icon_name):
        icon = None
        try: icon = ctk.CTkImage(Image.open(os.path.join(self.icon_path, icon_name)), size=(22, 22))
        except: pass
        
        btn = ctk.CTkButton(self, text=f"  {text}", image=icon, compound="left",
                            fg_color="transparent", text_color="#64748B", hover_color="#F1F5F9",
                            anchor="w", height=50, corner_radius=8, font=("DejaVu Sans", 14, "bold"),
                            command=lambda k=key: self.nav_click(k))
        btn.pack(fill="x", pady=2, padx=15)
        self.menu_btns[key] = btn

    def nav_click(self, key):
        for b in self.menu_btns.values(): b.configure(fg_color="transparent", text_color="#64748B")
        if key in self.menu_btns:
            self.menu_btns[key].configure(fg_color="#E0F2FE", text_color="#0284C7")
        self.on_navigate(key)