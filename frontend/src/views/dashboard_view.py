import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F8FAFC", scrollbar_button_color="#CBD5E1", 
                         scrollbar_button_hover_color="#94A3B8")
        self.FONT = "DejaVu Sans"
        
        self.grid_columnconfigure((0,1,2), weight=1)
        
        # Header với gradient effect
        self.create_header()
        
        # Loading animation
        self.loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loading_frame.grid(row=2, column=0, columnspan=3, pady=50)
        
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="⏳ Loading your dashboard...", 
                                         font=(self.FONT, 16), text_color="#64748B")
        self.loading_label.pack()
        
        self.progress = ctk.CTkProgressBar(self.loading_frame, width=300, height=4, 
                                          fg_color="#E2E8F0", progress_color="#3B82F6")
        self.progress.pack(pady=10)
        self.progress.set(0)
        self.animate_loading()
        
        threading.Thread(target=self.load).start()

    def create_header(self):
        """Header với gradient background effect"""
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=20, 
                             border_width=1, border_color="#E2E8F0")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=(0, 25))
        
        # Gradient bar
        gradient_bar = ctk.CTkFrame(header, height=6, fg_color="#3B82F6", corner_radius=20)
        gradient_bar.pack(fill="x")
        
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="x", padx=30, pady=20)
        
        user_name = api.user_info.get("full_name", "User")
        user_role = api.user_info.get("role", "STUDENT")
        
        # Avatar circle
        avatar_frame = ctk.CTkFrame(content, width=60, height=60, corner_radius=30, 
                                   fg_color="#E0F2FE", border_width=3, border_color="#3B82F6")
        avatar_frame.pack(side="left", padx=(0, 20))
        avatar_frame.pack_propagate(False)
        
        initial = user_name[0].upper() if user_name else "U"
        ctk.CTkLabel(avatar_frame, text=initial, font=(self.FONT, 24, "bold"), 
                    text_color="#0284C7").place(relx=0.5, rely=0.5, anchor="center")
        
        # User info
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(info_frame, text=f"Welcome back, {user_name}! 👋", 
                    font=(self.FONT, 26, "bold"), text_color="#1E293B", anchor="w").pack(anchor="w")
        
        subtitle_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        subtitle_frame.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(subtitle_frame, text="Your role: ", 
                    font=(self.FONT, 13), text_color="#64748B").pack(side="left")
        
        role_colors = {"STUDENT": "#3B82F6", "CVHT": "#F59E0B", "ADMIN": "#EF4444"}
        role_bg = role_colors.get(user_role, "#64748B")
        role_badge = ctk.CTkLabel(subtitle_frame, text=f"  {user_role}  ", 
                                 font=(self.FONT, 11, "bold"),
                                 text_color="white", fg_color=role_bg, corner_radius=12)
        role_badge.pack(side="left", padx=5)

    def animate_loading(self):
        """Animate loading bar"""
        current = self.progress.get()
        if current < 0.9:
            self.progress.set(current + 0.1)
            self.after(100, self.animate_loading)

    def load(self):
        data = api.get_dashboard_stats()
        self.after(0, lambda: self.render(data))

    def render(self, data):
        self.loading_frame.destroy()
        self.progress.set(1.0)
        
        role = data.get("role", api.user_info.get("role", "STUDENT"))
        
        if role == "STUDENT":
            self.render_student(data)
        elif role in ["CVHT", "ADMIN"]:
            self.render_manager(data)

    def create_stat_card(self, col, title, value, color, icon="📊"):
        """Modern stat card with icon and hover effect"""
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=16, 
                           border_width=1, border_color="#E2E8F0")
        card.grid(row=1, column=col, sticky="nsew", padx=12, pady=10)
        
        # Color accent bar
        accent = ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=16)
        accent.pack(fill="x")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon circle
        icon_bg = ctk.CTkFrame(content, width=50, height=50, corner_radius=25, 
                              fg_color=f"{color}20")  # 20% opacity
        icon_bg.pack(anchor="w", pady=(0, 15))
        icon_bg.pack_propagate(False)
        
        ctk.CTkLabel(icon_bg, text=icon, font=(self.FONT, 24)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        ctk.CTkLabel(content, text=title, font=(self.FONT, 13, "bold"), 
                    text_color="#64748B", anchor="w").pack(anchor="w", fill="x")
        
        # Value
        ctk.CTkLabel(content, text=str(value), font=(self.FONT, 32, "bold"), 
                    text_color=color, anchor="w").pack(anchor="w", fill="x", pady=(5, 0))

    def create_chart_container(self, title, subtitle=""):
        """Modern chart container"""
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=16, 
                                border_width=1, border_color="#E2E8F0")
        container.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=20, padx=12)
        
        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(header, text=title, font=(self.FONT, 18, "bold"), 
                    text_color="#1E293B", anchor="w").pack(side="left")
        
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, font=(self.FONT, 12), 
                        text_color="#94A3B8", anchor="e").pack(side="right")
        
        return container

    def render_student(self, d):
        """Student dashboard with modern cards"""
        # Stats cards
        self.create_stat_card(0, "GPA Score", f"{d.get('gpa_4', 0.0):.2f}/4.0", "#10B981", "🎯")
        self.create_stat_card(1, "Credits Earned", f"{d.get('credits', 0)}", "#3B82F6", "📚")
        
        status = "Paid ✓" if d.get('tuition_status', False) else "Pending"
        status_color = "#10B981" if d.get('tuition_status', False) else "#EF4444"
        self.create_stat_card(2, "Tuition Status", status, status_color, "💳")
        
        # Performance chart
        if d.get('semester_grades'):
            container = self.create_chart_container("📈 Academic Performance Trend", 
                                                   "Your GPA progress over semesters")
            
            fig = Figure(figsize=(10, 4), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            semesters = list(range(1, len(d['semester_grades']) + 1))
            grades = d['semester_grades']
            
            # Gradient fill
            ax.fill_between(semesters, grades, alpha=0.2, color='#3B82F6')
            ax.plot(semesters, grades, marker='o', color='#3B82F6', linewidth=3, 
                   markersize=10, markerfacecolor='white', markeredgewidth=2, 
                   markeredgecolor='#3B82F6')
            
            ax.set_ylim(0, 4.2)
            ax.set_xlabel('Semester', fontsize=11, color='#64748B')
            ax.set_ylabel('GPA', fontsize=11, color='#64748B')
            ax.grid(color='#F1F5F9', linestyle='--', linewidth=0.5, alpha=0.7)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E2E8F0')
            ax.spines['bottom'].set_color('#E2E8F0')
            
            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def render_manager(self, d):
        """Manager dashboard with analytics"""
        # Stats cards
        self.create_stat_card(0, "Total Students", d.get('total_students', 0), "#3B82F6", "👥")
        self.create_stat_card(1, "Academic Warnings", d.get('warning_count', 0), "#EF4444", "⚠️")
        self.create_stat_card(2, "Tuition Debt", d.get('debt_count', 0), "#F59E0B", "💰")
        
        # Distribution charts
        dist = d.get('gpa_distribution', {})
        if dist and any(dist.values()):
            container = self.create_chart_container("📊 Grade Distribution Analysis", 
                                                   "Student performance breakdown")
            
            fig = Figure(figsize=(12, 4.5), dpi=100, facecolor='white')
            
            # Pie chart
            ax1 = fig.add_subplot(121)
            labels = list(dist.keys())
            values = list(dist.values())
            colors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']
            
            wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%', 
                                               colors=colors, startangle=90,
                                               textprops={'fontsize': 10, 'weight': 'bold'})
            for autotext in autotexts:
                autotext.set_color('white')
            ax1.set_title('Distribution by Category', fontsize=12, color='#1E293B', pad=15)
            
            # Bar chart
            ax2 = fig.add_subplot(122)
            bars = ax2.bar(labels, values, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            ax2.set_ylabel('Number of Students', fontsize=11, color='#64748B')
            ax2.set_title('Students per Grade Level', fontsize=12, color='#1E293B', pad=15)
            ax2.grid(axis='y', alpha=0.3, linestyle='--', color='#E2E8F0')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#E2E8F0')
            ax2.spines['bottom'].set_color('#E2E8F0')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1E293B')
            
            fig.tight_layout(pad=3)
            
            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=25, pady=(0, 20))
        else:
            # Empty state
            empty_container = self.create_chart_container("📊 Grade Distribution", "No data available")
            empty_frame = ctk.CTkFrame(empty_container, fg_color="#F8FAFC", corner_radius=12)
            empty_frame.pack(fill="both", expand=True, padx=25, pady=25)
            
            ctk.CTkLabel(empty_frame, text="📭", font=(self.FONT, 48)).pack(pady=(30, 10))
            ctk.CTkLabel(empty_frame, text="No grade data available yet", 
                        font=(self.FONT, 16, "bold"), text_color="#64748B").pack()
            ctk.CTkLabel(empty_frame, text="Import grades to see analytics here", 
                        font=(self.FONT, 12), text_color="#94A3B8").pack(pady=(5, 30))
