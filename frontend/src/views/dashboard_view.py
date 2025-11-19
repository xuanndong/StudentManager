import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardView(ctk.CTkScrollableFrame): 
    def __init__(self, master):
        # Cấu hình ẩn Scrollbar: set chiều rộng cực nhỏ hoặc màu trùng nền
        super().__init__(master, fg_color="transparent", 
                         scrollbar_button_color="#F8FAFC",  # Trùng màu nền Dashboard
                         scrollbar_button_hover_color="#F8FAFC") 
        
        # Font chuẩn Linux (Fix lỗi vỡ hạt)
        self.FONT_FAMILY = "DejaVu Sans"
        self.FONT_BOLD = (self.FONT_FAMILY, 32, "bold")
        self.FONT_TITLE = (self.FONT_FAMILY, 18, "bold")
        self.FONT_TEXT = (self.FONT_FAMILY, 14)

        # Layout Grid chung
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        
        # 1. Title Section
        user_name = api.user_info.get("full_name", "User")
        self.lbl_welcome = ctk.CTkLabel(self, text=f"Overview for {user_name}", 
                                      font=(self.FONT_FAMILY, 22, "bold"), text_color="#334155")
        self.lbl_welcome.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 20))

        # Loading
        self.loading_lbl = ctk.CTkLabel(self, text="Loading data...", font=self.FONT_TEXT, text_color="gray")
        self.loading_lbl.grid(row=1, column=0, columnspan=3)

        # Load Data
        threading.Thread(target=self.load_data).start()

    def load_data(self):
        data = api.get_dashboard_stats()
        self.after(0, lambda: self.update_ui(data))

    def update_ui(self, data):
        self.loading_lbl.destroy()
        
        role = data.get("role", "STUDENT")

        if role == "STUDENT":
            self.setup_student_ui(data)
        else:
            self.setup_manager_ui(data)

    # ==========================================
    # UI CHO SINH VIÊN (STUDENT)
    # ==========================================
    def setup_student_ui(self, data):
        # Card 1: GPA
        self.create_info_card(0, "Overall GPA (4.0)", str(data['gpa_4']), "#10B981") # Xanh lá
        
        # Card 2: Tín chỉ
        self.create_info_card(1, "Total Credits", str(data['credits']), "#3B82F6") # Xanh dương
        
        # Card 3: Học phí
        status = "Paid" if data['tuition_status'] else "Unpaid"
        color = "#10B981" if data['tuition_status'] else "#EF4444"
        self.create_info_card(2, "Tuition Status", status, color)

        # Biểu đồ đường (Line Chart) theo dõi tiến độ
        self.create_chart_frame("Academic Progress (Last 5 Semesters)")
        self.draw_line_chart(data['semester_grades'])

    # ==========================================
    # UI CHO CVHT / ADMIN (MANAGER)
    # ==========================================
    def setup_manager_ui(self, data):
        # Card 1: Tổng SV
        self.create_info_card(0, "Total Students", str(data['total_students']), "#3B82F6")
        
        # Card 2: Cảnh báo
        self.create_info_card(1, "Academic Warnings", str(data['warning_count']), "#EF4444")
        
        # Card 3: Nợ phí
        self.create_info_card(2, "Tuition Debt", str(data['debt_count']), "#F59E0B")

        # Biểu đồ tròn (Pie Chart) phân bố điểm
        self.create_chart_frame("Class GPA Distribution")
        self.draw_pie_chart(data['gpa_distribution'])

    # ==========================================
    # CÁC HÀM DÙNG CHUNG (HELPER)
    # ==========================================
    def create_info_card(self, col, title, value, color):
        """Tạo thẻ hiển thị số liệu"""
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        card.grid(row=1, column=col, sticky="ew", padx=10)
        
        # Vạch màu điểm nhấn
        line = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=4)
        line.pack(side="left", fill="y", padx=(0, 15), pady=2)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", pady=20, padx=5)
        
        lbl_title = ctk.CTkLabel(content, text=title, font=self.FONT_TEXT, text_color="#64748B")
        lbl_title.pack(anchor="w")
        
        lbl_value = ctk.CTkLabel(content, text=value, font=self.FONT_BOLD, text_color="#1E293B")
        lbl_value.pack(anchor="w")

    def create_chart_frame(self, title):
        """Tạo khung chứa biểu đồ"""
        self.chart_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.chart_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=30, padx=10)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.chart_frame, text=title, 
                     font=self.FONT_TITLE, text_color="#475569").pack(pady=15)

    def draw_pie_chart(self, gpa_data):
        labels = ['Excellent', 'Good', 'Fair', 'Average', 'Weak']
        values = [
            gpa_data.get('excellent', 0),
            gpa_data.get('good', 0),
            gpa_data.get('fair', 0),
            gpa_data.get('average', 0),
            gpa_data.get('weak', 0)
        ]
        colors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']

        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                          startangle=90, colors=colors,
                                          textprops={'color':"#333", 'fontsize': 9, 'fontname': "DejaVu Sans"})
        
        for text in autotexts:
            text.set_color('white')
            text.set_weight('bold')

        ax.axis('equal')
        
        # Nhúng vào Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def draw_line_chart(self, grades):
        semesters = [f"Sem {i+1}" for i in range(len(grades))]
        
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Vẽ đường
        ax.plot(semesters, grades, marker='o', linestyle='-', color='#3B82F6', linewidth=2, markersize=8)
        
        # Grid nhẹ
        ax.grid(color='#E2E8F0', linestyle='--', linewidth=0.5)
        
        # Label
        ax.set_ylim(0, 4.0)
        ax.set_ylabel("GPA", fontsize=10, fontname="DejaVu Sans")
        
        # Style trục
        for spine in ax.spines.values():
            spine.set_edgecolor('#CBD5E1')
            
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))