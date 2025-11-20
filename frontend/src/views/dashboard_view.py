import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent", scrollbar_button_color="#F1F5F9")
        self.FONT = "DejaVu Sans"
        self.grid_columnconfigure((0,1,2), weight=1)
        
        self.loading = ctk.CTkLabel(self, text="Loading...", text_color="gray")
        self.loading.grid(row=0, column=1, pady=50)
        
        threading.Thread(target=self.load).start()

    def load(self):
        data = api.get_dashboard_stats()
        self.after(0, lambda: self.render(data))

    def render(self, data):
        self.loading.destroy()
        role = data.get("role", "STUDENT")
        
        if role == "STUDENT":
            self.card(0, "GPA", data.get('gpa_4', 0), "#10B981")
            self.card(1, "Credits", data.get('credits', 0), "#3B82F6")
            st = "Paid" if data.get('tuition_status') else "Debt"
            self.card(2, "Tuition", st, "#F59E0B" if st=="Debt" else "#10B981")
            self.draw_chart(data.get('semester_grades', []), "line")
        else:
            self.card(0, "Students", data.get('total_students', 0), "#3B82F6")
            self.card(1, "Warnings", data.get('warning_count', 0), "#EF4444")
            self.card(2, "Tuition Debt", data.get('debt_count', 0), "#F59E0B")
            self.draw_chart(data.get('gpa_distribution', {}), "pie")

    def card(self, col, title, val, color):
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        f.grid(row=0, column=col, sticky="ew", padx=10, pady=10)
        ctk.CTkFrame(f, width=5, fg_color=color, corner_radius=5).pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkLabel(f, text=title, font=(self.FONT, 12), text_color="#64748B").pack(anchor="w", pady=(15,0))
        ctk.CTkLabel(f, text=str(val), font=(self.FONT, 24, "bold"), text_color="#1E293B").pack(anchor="w", pady=(0,15))

    def draw_chart(self, data, chart_type):
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        f.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=20)
        
        fig = Figure(figsize=(8, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        if chart_type == "line":
            ax.plot(data, marker='o', color='#3B82F6', linewidth=2)
            ax.set_title("Academic Trend")
        else:
            ax.pie(list(data.values()), labels=list(data.keys()), autopct='%1.1f%%')
            ax.set_title("Grade Distribution")
            
        canvas = FigureCanvasTkAgg(fig, master=f)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)