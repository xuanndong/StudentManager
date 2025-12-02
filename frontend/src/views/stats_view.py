import customtkinter as ctk
from src.api.client import api
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "Ubuntu"
        self.selected_class_id = None
        self._destroyed = False
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Thống kê lớp học", font=(self.FONT, 24, "bold"), text_color="#334155").pack(side="left")
        
        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")
        
        self.class_map = {}
        self.cb_class = ctk.CTkComboBox(controls, values=["Đang tải..."], width=200, command=self.on_class_change)
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
        threading.Thread(target=self.load_classes, daemon=True).start()

    def load_classes(self):
        classes = api.get_my_classes()
        if classes and not self._destroyed:
            self.class_map = {c['name']: c['_id'] for c in classes}
            names = list(self.class_map.keys())
            try:
                self.cb_class.configure(values=names)
                if names:
                    self.cb_class.set(names[0])
                    self.selected_class_id = self.class_map[names[0]]
                    if not self._destroyed:
                        self.after(0, lambda: self.refresh(None) if not self._destroyed else None)
            except:
                pass  # Widget destroyed

    def on_class_change(self, choice):
        self.selected_class_id = self.class_map.get(choice)
        self.refresh(None)

    def refresh(self, _):
        for widget in self.content.winfo_children():
            widget.destroy()
        
        if not self.selected_class_id:
            ctk.CTkLabel(self.content, text="Vui lòng chọn một lớp").pack(pady=20)
            return
        
        loading = ctk.CTkLabel(self.content, text="Đang tải thống kê...", text_color="gray")
        loading.grid(row=0, column=1, pady=20)
        
        threading.Thread(target=lambda: self.load_stats(loading), daemon=True).start()

    def load_stats(self, loading_lbl):
        stats = api.get_class_stats(self.selected_class_id, self.sem_var.get())
        if not self._destroyed:
            try:
                self.after(0, lambda: self.render(stats, loading_lbl) if not self._destroyed else None)
            except:
                pass  # Widget destroyed

    def render(self, stats, loading_lbl):
        if self._destroyed:
            return
        try:
            loading_lbl.destroy()
        except:
            pass  # Already destroyed
        
        if not stats:
            ctk.CTkLabel(self.content, text="Không có dữ liệu").grid(row=0, column=1, pady=20)
            return
        
        # Cards
        self.card(0, "Tổng số sinh viên", stats.get('total_students', 0), "#3B82F6")
        self.card(1, "Cảnh báo học vụ", stats.get('warning_count', 0), "#EF4444")
        self.card(2, "Nợ học phí", stats.get('debt_count', 0), "#F59E0B")
        
        # GPA Distribution Chart
        chart_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=15)
        chart_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=20, padx=10)
        
        ctk.CTkLabel(chart_frame, text="Phân bố điểm trung bình", font=(self.FONT, 16, "bold"), 
                     text_color="#475569").pack(pady=15)
        
        dist = stats.get('gpa_distribution', {})
        if dist:
            # Simple bar chart only with better margins
            fig = plt.figure(figsize=(10, 5), dpi=90)
            fig.patch.set_facecolor('white')
            
            # Add subplot with custom position to leave room for labels
            ax = fig.add_subplot(111)
            
            # Define grade categories in order
            grade_order = ['Xuất sắc', 'Giỏi', 'Khá', 'Trung bình', 'Yếu']
            colors_map = {
                'Xuất sắc': '#10B981',
                'Giỏi': '#3B82F6', 
                'Khá': '#8B5CF6',
                'Trung bình': '#F59E0B',
                'Yếu': '#EF4444'
            }
            
            # Prepare data in correct order
            labels = []
            values = []
            colors = []
            
            for grade in grade_order:
                if grade in dist:
                    labels.append(grade)
                    values.append(dist[grade])
                    colors.append(colors_map[grade])
            
            # Create bar chart
            bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor='white', linewidth=2)
            
            # Styling with better font sizes
            ax.set_ylabel('Số lượng sinh viên', fontsize=11, fontweight='bold', labelpad=10)
            ax.set_xlabel('Xếp loại học lực', fontsize=11, fontweight='bold', labelpad=10)
            ax.set_title('Phân bố xếp loại học lực của lớp', fontsize=13, fontweight='bold', pad=15)
            ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)
            
            # Rotate x labels if needed
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            # Set y-axis to start from 0
            ax.set_ylim(bottom=0)
            
            # Adjust layout with more padding to prevent label cutoff
            plt.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
            
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def card(self, col, title, val, color):
        f = ctk.CTkFrame(self.content, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        f.grid(row=0, column=col, sticky="ew", padx=10, pady=5)
        
        # Vertical layout for better small screen support
        ctk.CTkFrame(f, height=5, fg_color=color, corner_radius=5).pack(fill="x", padx=5, pady=(5, 0))
        
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(fill="both", expand=True, pady=15, padx=15)
        
        ctk.CTkLabel(box, text=title, font=(self.FONT, 12), text_color="#64748B", 
                    wraplength=180, justify="center").pack(anchor="center")
        ctk.CTkLabel(box, text=str(val), font=(self.FONT, 24, "bold"), 
                    text_color="#1E293B").pack(anchor="center", pady=(5, 0))
    
    def destroy(self):
        self._destroyed = True
        # Close any matplotlib figures
        try:
            plt.close('all')
        except:
            pass
        super().destroy()
