import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardView(ctk.CTkScrollableFrame): 
    def __init__(self, master):
        super().__init__(master, fg_color="transparent", scrollbar_button_color="#F8FAFC", scrollbar_button_hover_color="#F8FAFC") 
        self.FONT = "DejaVu Sans"
        
        self.grid_columnconfigure((0,1,2), weight=1)
        
        user_name = api.user_info.get("full_name", "User")
        user_role = api.user_info.get("role", "STUDENT")
        
        # Welcome message với role badge
        welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        welcome_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 20))
        
        ctk.CTkLabel(welcome_frame, text=f"Hello, {user_name} 👋", 
                     font=(self.FONT, 24, "bold"), text_color="#334155").pack(side="left")
        
        role_colors = {"STUDENT": "#3B82F6", "CVHT": "#F59E0B", "ADMIN": "#EF4444"}
        role_bg = role_colors.get(user_role, "#64748B")
        role_badge = ctk.CTkLabel(welcome_frame, text=user_role, font=(self.FONT, 11, "bold"),
                                  text_color="white", fg_color=role_bg, corner_radius=5)
        role_badge.pack(side="left", padx=10, pady=5, ipadx=10, ipady=3)
        
        self.loading = ctk.CTkLabel(self, text="Loading data...", text_color="gray")
        self.loading.grid(row=1, column=0, columnspan=3)
        
        threading.Thread(target=self.load).start()

    def load(self):
        data = api.get_dashboard_stats()
        self.after(0, lambda: self.render(data))

    def render(self, data):
        self.loading.destroy()
        role = data.get("role", api.user_info.get("role", "STUDENT"))
        
        if role == "STUDENT":
            self.render_student(data)
        elif role in ["CVHT", "ADMIN"]:
            self.render_manager(data)

    def card(self, col, title, val, color):
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        f.grid(row=1, column=col, sticky="ew", padx=10)
        ctk.CTkFrame(f, width=5, fg_color=color, corner_radius=5).pack(side="left", fill="y", padx=(0, 15), pady=5)
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(side="left", pady=20, padx=10)
        ctk.CTkLabel(box, text=title, font=(self.FONT, 13), text_color="#64748B").pack(anchor="w")
        ctk.CTkLabel(box, text=str(val), font=(self.FONT, 28, "bold"), text_color="#1E293B").pack(anchor="w")

    def chart_box(self, title):
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        f.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=30, padx=10)
        ctk.CTkLabel(f, text=title, font=(self.FONT, 16, "bold"), text_color="#475569").pack(pady=15)
        return f

    def render_student(self, d):
        self.card(0, "GPA (4.0)", f"{d.get('gpa_4', 0.0):.2f}", "#10B981")
        self.card(1, "Credits", d.get('credits', 0), "#3B82F6")
        status = "Paid" if d.get('tuition_status', False) else "Debt"
        self.card(2, "Tuition", status, "#10B981" if d.get('tuition_status', False) else "#EF4444")
        
        # Chart chỉ hiện nếu có dữ liệu
        if d.get('semester_grades'):
            box = self.chart_box("Academic Performance Trend")
            fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
            fig.patch.set_facecolor('white')
            ax.plot(d['semester_grades'], marker='o', color='#3B82F6', linewidth=2, markersize=8)
            ax.set_ylim(0, 4)
            ax.set_ylabel('GPA')
            ax.set_xlabel('Semester')
            ax.grid(color='#F1F5F9', alpha=0.5)
            for s in ax.spines.values(): s.set_visible(False)
            canvas = FigureCanvasTkAgg(fig, master=box)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    def render_manager(self, d):
        self.card(0, "Total Students", d.get('total_students', 0), "#3B82F6")
        self.card(1, "Warnings", d.get('warning_count', 0), "#EF4444")
        self.card(2, "Tuition Debt", d.get('debt_count', 0), "#F59E0B")
        
        dist = d.get('gpa_distribution', {})
        if dist and any(dist.values()):
            box = self.chart_box("Grade Distribution Overview")
            fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
            fig.patch.set_facecolor('white')
            
            labels = list(dist.keys())
            vals = list(dist.values())
            colors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']
            
            ax.pie(vals, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax.set_title('Student Distribution by GPA Category')
            
            canvas = FigureCanvasTkAgg(fig, master=box)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)
        else:
            info = ctk.CTkLabel(self, text="No grade data available yet", 
                               font=(self.FONT, 14), text_color="#94A3B8")
            info.grid(row=2, column=0, columnspan=3, pady=30)