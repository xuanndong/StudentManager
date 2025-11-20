import customtkinter as ctk
from src.components.sidebar import Sidebar
from src.views.dashboard_view import DashboardView
from src.views.classes_view import ClassesView
from src.views.grades_view import GradesView
from src.views.chat_view import ChatView
from src.views.forum_view import ForumView
from src.views.users_view import UsersView
from src.views.stats_view import StatsView
from src.api.client import api

class MainView(ctk.CTkFrame):
    def __init__(self, master, on_logout):
        super().__init__(master)
        self.on_logout = on_logout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, on_navigate=self.switch, on_logout=self.handle_logout)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Content
        self.content = ctk.CTkFrame(self, fg_color="#F8FAFC")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.content, height=70, fg_color="white", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.lbl_title = ctk.CTkLabel(self.header, text="Dashboard", font=("DejaVu Sans", 24, "bold"), text_color="#334155")
        self.lbl_title.pack(side="left", padx=30, pady=20)

        # View Area
        self.view_area = ctk.CTkFrame(self.content, fg_color="transparent")
        self.view_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        self.switch("dashboard")

    def switch(self, key):
        for w in self.view_area.winfo_children(): w.destroy()
        
        # Set Title
        titles = {
            "dashboard": "Dashboard", "classes": "Classes", "grades": "Grades",
            "forum": "Forum", "chat": "Messages", "stats": "Statistics", "users": "User Management"
        }
        self.lbl_title.configure(text=titles.get(key, "Dashboard"))

        # Render View
        views = {
            "dashboard": DashboardView, "classes": ClassesView, "grades": GradesView,
            "forum": ForumView, "chat": ChatView, "stats": StatsView, "users": UsersView
        }
        
        if key in views:
            views[key](self.view_area).pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.view_area, text="Not Found").pack()

    def handle_logout(self):
        api.logout()
        self.on_logout()