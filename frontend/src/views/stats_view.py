import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "DejaVu Sans"
        self.selected_class_id = None
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Class Statistics", font=(self.FONT, 24, "bold"), text_color="#334155").pack(side="left")
        
        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")
        
        self.class_map = {}
        self.cb_class = ctk.CTkComboBox(controls, values=["Loading..."], width=200, command=self.on_class_change)
        self.cb_class.pack(side="left", padx=10)
        
        self.sem_var = ctk.StringVar(value="2025-1")
        self.cb_sem = ctk.CTkComboBox(controls, values=["2024-1", "2024-2", "2025-1"], 
                                      width=120, variable=self.sem_var, command=self.refresh)
        self.cb_sem.pack(side="left", padx=10)
        
        ctk.CTkButton(controls, text="↻", width=40, fg_color="#94A3B8", 
                      command=lambda: self.refresh(None)).pack(side="left")
        
        # Content Area
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        self.content.grid_columnconfigure((0,1,2), weight=1)
        
        # Load classes
        threading.Thread(target=self.load_classes).start()

    def load_classes(self):
        classes = api.get_my_classes()
        if classes:
            self.class_map = {c['name']: c['_id'] for c in classes}
            names = list(self.class_map.keys())
            self.cb_class.configure(values=names)
            if names:
                self.cb_class.set(names[0])
                self.selected_class_id = self.class_map[names[0]]
                self.after(0, lambda: self.refresh(None))

    def on_class_change(self, choice):
        self.selected_class_id = self.class_map.get(choice)
        self.refresh(None)

    def refresh(self, _):
        for widget in self.content.winfo_children():
            widget.destroy()
        
        if not self.selected_class_id:
            ctk.CTkLabel(self.content, text="Please select a class").pack(pady=20)
            return
        
        loading = ctk.CTkLabel(self.content, text="Loading statistics...", text_color="gray")
        loading.grid(row=0, column=1, pady=20)
        
        threading.Thread(target=lambda: self.load_stats(loading)).start()

    def load_stats(self, loading_lbl):
        stats = api.get_class_stats(self.selected_class_id, self.sem_var.get())
        self.after(0, lambda: self.render(stats, loading_lbl))

    def render(self, stats, loading_lbl):
        loading_lbl.destroy()
        
        if not stats:
            ctk.CTkLabel(self.content, text="No data available").grid(row=0, column=1, pady=20)
            return
        
        # Cards
        self.card(0, "Total Students", stats.get('total_students', 0), "#3B82F6")
        self.card(1, "Academic Warnings", stats.get('warning_count', 0), "#EF4444")
        self.card(2, "Tuition Debt", stats.get('debt_count', 0), "#F59E0B")
        
        # GPA Distribution Chart
        chart_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=15)
        chart_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=20, padx=10)
        
        ctk.CTkLabel(chart_frame, text="GPA Distribution", font=(self.FONT, 16, "bold"), 
                     text_color="#475569").pack(pady=15)
        
        dist = stats.get('gpa_distribution', {})
        if dist:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), dpi=100)
            fig.patch.set_facecolor('white')
            
            # Pie Chart
            labels = list(dist.keys())
            values = list(dist.values())
            colors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']
            ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax1.set_title('Grade Distribution')
            
            # Bar Chart
            ax2.bar(labels, values, color=colors)
            ax2.set_ylabel('Number of Students')
            ax2.set_title('Students per Grade Category')
            ax2.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    def card(self, col, title, val, color):
        f = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        f.grid(row=0, column=col, sticky="ew", padx=10)
        
        ctk.CTkFrame(f, width=5, fg_color=color, corner_radius=5).pack(side="left", fill="y", padx=(0, 15), pady=5)
        
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(side="left", pady=20, padx=10)
        
        ctk.CTkLabel(box, text=title, font=(self.FONT, 13), text_color="#64748B").pack(anchor="w")
        ctk.CTkLabel(box, text=str(val), font=(self.FONT, 28, "bold"), text_color="#1E293B").pack(anchor="w")
