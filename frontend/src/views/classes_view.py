import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox, filedialog

class ClassesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "DejaVu Sans"
        self.role = api.user_info.get("role")
        
        # Header
        top = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        top.pack(fill="x", padx=10, pady=10)
        
        if self.role == "CVHT":
            ctk.CTkButton(top, text="+ Create Class", fg_color="#3B82F6", width=120,
                          command=self.popup_create).pack(side="right", padx=20, pady=15)

        self.grid_layout = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_layout.pack(fill="both", expand=True, padx=10)
        self.grid_layout.grid_columnconfigure((0,1,2), weight=1)
        
        self.refresh()

    def refresh(self):
        for w in self.grid_layout.winfo_children(): w.destroy()
        threading.Thread(target=self.load).start()

    def load(self):
        data = api.get_my_classes()
        self.after(0, lambda: self.render(data))

    def render(self, classes):
        if not classes:
            ctk.CTkLabel(self.grid_layout, text="No classes found").pack(pady=20)
            return
        for i, c in enumerate(classes):
            self.card(c, i//3, i%3)

    def card(self, data, r, c):
        f = ctk.CTkFrame(self.grid_layout, fg_color="white", corner_radius=12)
        f.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
        
        # Accent Header
        ctk.CTkFrame(f, height=5, fg_color="#6366F1").pack(fill="x")
        
        # Content
        ctk.CTkLabel(f, text=data['name'], font=(self.FONT, 16, "bold"), text_color="#1E293B").pack(pady=(15,5))
        ctk.CTkLabel(f, text=data['semester'], font=(self.FONT, 12), text_color="gray").pack()
        
        btn = ctk.CTkButton(f, text="Manage" if self.role=="CVHT" else "View", 
                            fg_color="#F1F5F9", text_color="#334155", hover_color="#E2E8F0",
                            command=lambda: self.detail(data))
        btn.pack(fill="x", padx=20, pady=15)

    def detail(self, data):
        # Popup chi tiết
        top = ctk.CTkToplevel(self)
        top.geometry("600x500")
        top.title(data['name'])
        top.configure(fg_color="white")
        
        # List SV
        scroll = ctk.CTkScrollableFrame(top, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        if self.role == "CVHT":
            ctk.CTkButton(top, text="Import Student List (Excel)", command=lambda: self.import_sv(data['_id'], top)).pack(pady=10)

        # Load students
        def load_sv():
            sv = api.get_class_students(data['_id'])
            top.after(0, lambda: render_sv(sv))
            
        def render_sv(sv_list):
            for s in sv_list:
                row = ctk.CTkFrame(scroll, fg_color="#F8FAFC")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"{s['mssv']} - {s.get('full_name', '')}", width=300, anchor="w").pack(side="left", padx=10)
                if self.role == "CVHT":
                    ctk.CTkButton(row, text="Kick", width=50, fg_color="#EF4444", 
                                  command=lambda uid=s['_id']: self.kick(data['_id'], uid, top)).pack(side="right", padx=5)
        
        threading.Thread(target=load_sv).start()

    def popup_create(self):
        # (Code popup tạo lớp như cũ)
        pass

    def import_sv(self, cid, top):
        path = filedialog.askopenfilename()
        if path:
            ok, res = api.import_students(cid, path)
            messagebox.showinfo("Result", "Imported!" if ok else "Error")
            top.destroy()

    def kick(self, cid, uid, top):
        if api.remove_student(cid, uid):
            top.destroy()
            messagebox.showinfo("Success", "Removed")