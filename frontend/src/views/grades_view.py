import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import filedialog, messagebox

class GradesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "Ubuntu"
        self.role = api.user_info.get("role")
        
        # Header & Filter
        head = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        head.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(head, text="Grade Board", font=(self.FONT, 20, "bold"), text_color="#334155").pack(side="left", padx=20, pady=15)
        
        self.sem_var = ctk.StringVar(value="2025-1")
        ctk.CTkComboBox(head, values=["2024-1", "2024-2", "2025-1"], variable=self.sem_var, 
                        command=self.refresh, width=100).pack(side="right", padx=10)
        
        self.selected_class = None
        if self.role == "CVHT":
            self.cb_class = ctk.CTkComboBox(head, values=["Loading..."], width=150, command=self.on_cls_change)
            self.cb_class.pack(side="right", padx=10)
            ctk.CTkButton(head, text="Import Excel", fg_color="#10B981", width=100, 
                          command=self.import_excel).pack(side="right", padx=10)
            self.class_map = {}
            threading.Thread(target=self.load_classes, daemon=True).start()

        # Table
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        self.scroll.pack(fill="both", expand=True)
        
        # Table Header
        cols = ["Semester", "GPA", "Credits", "Debt", "Warning"]
        if self.role == "CVHT": cols.insert(0, "MSSV")
        
        h_row = ctk.CTkFrame(self.scroll, fg_color="#F1F5F9", height=40)
        h_row.pack(fill="x")
        for c in cols:
            ctk.CTkLabel(h_row, text=c, font=(self.FONT, 12, "bold"), text_color="#475569").pack(side="left", expand=True, fill="x")

        if self.role == "STUDENT": self.refresh(None)

    def load_classes(self):
        cls = api.get_my_classes()
        if cls:
            self.class_map = {c['name']: c['_id'] for c in cls}
            names = list(self.class_map.keys())
            self.cb_class.configure(values=names)
            if names:
                self.cb_class.set(names[0])
                self.selected_class = self.class_map[names[0]]
                self.refresh(None)

    def on_cls_change(self, val):
        self.selected_class = self.class_map.get(val)
        self.refresh(None)

    def refresh(self, _):
        for w in self.scroll.winfo_children():
            if isinstance(w, ctk.CTkFrame) and w != self.scroll.winfo_children()[0]: # Giữ lại header
                w.destroy()
        
        threading.Thread(target=self.fetch, daemon=True).start()

    def fetch(self):
        sem = self.sem_var.get()
        data = []
        if self.role == "STUDENT":
            data = api.get_my_grades(sem)
        elif self.selected_class:
            data = api.get_class_grades(self.selected_class, sem)
        
        self.after(0, lambda: self.render(data))

    def render(self, data):
        if not data:
            ctk.CTkLabel(self.scroll, text="No data").pack(pady=20)
            return
            
        for r in data:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            vals = [r['semester'], f"{r.get('gpa',0):.2f}", str(r.get('credits_earned',0)), 
                    "YES" if r.get('tuition_debt') else "NO", 
                    str(r.get('academic_warning',0))]
            if self.role == "CVHT": vals.insert(0, r.get('student_id', 'N/A'))
            
            for i, v in enumerate(vals):
                col = "black"
                if "YES" in v or (i == len(vals)-1 and v != "0"): col = "#EF4444"
                ctk.CTkLabel(row, text=v, text_color=col, font=(self.FONT, 12)).pack(side="left", expand=True, fill="x")
            
            ctk.CTkFrame(self.scroll, height=1, fg_color="#E2E8F0").pack(fill="x")

    def import_excel(self):
        if not self.selected_class: return
        path = filedialog.askopenfilename()
        if path:
            ok, res = api.import_grades(self.selected_class, self.sem_var.get(), path)
            msg = f"Success: {res.get('success_count')}" if ok else f"Error: {res}"
            messagebox.showinfo("Import", msg)
            self.refresh(None)