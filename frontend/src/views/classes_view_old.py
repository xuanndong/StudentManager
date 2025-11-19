import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox, filedialog

class ClassesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "DejaVu Sans"
        
        # Header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(head, text="My Classes", font=(self.FONT, 24, "bold"), text_color="#334155").pack(side="left")

        # Chỉ CVHT mới thấy nút tạo lớp
        if api.user_info.get("role") == "CVHT":
            ctk.CTkButton(head, text="+ New Class", font=(self.FONT, 14, "bold"), fg_color="#3B82F6", 
                          command=self.popup_create).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.scroll.grid_columnconfigure((0,1,2), weight=1)
        
        self.loading = ctk.CTkLabel(self.scroll, text="Loading...", text_color="gray")
        self.loading.grid(row=0, column=1, pady=20)
        
        threading.Thread(target=self.load).start()

    def load(self):
        data = api.get_my_classes()
        self.after(0, lambda: self.render(data))

    def render(self, classes):
        self.loading.destroy()
        if not classes:
            ctk.CTkLabel(self.scroll, text="No classes found").grid(row=0, column=1)
            return
            
        for i, c in enumerate(classes):
            self.card(c, i//3, i%3)

    def card(self, data, r, c):
        f = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        f.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkFrame(f, height=6, fg_color="#6366F1", corner_radius=5).pack(fill="x")
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(box, text=data.get("name"), font=(self.FONT, 16, "bold"), text_color="#1E293B", anchor="w").pack(fill="x")
        ctk.CTkLabel(box, text=data.get("semester"), font=(self.FONT, 12), text_color="gray", anchor="w").pack(fill="x")
        ctk.CTkLabel(box, text=f"Students: {len(data.get('student_ids', []))}", font=(self.FONT, 11), text_color="#64748B", anchor="w").pack(fill="x", pady=(5,0))
        
        ctk.CTkButton(f, text="View Details →", fg_color="#F1F5F9", text_color="#334155", hover_color="#E2E8F0", 
                      command=lambda d=data: self.open_class_detail(d)).pack(fill="x", padx=15, pady=15)

    def open_class_detail(self, class_data):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Class: {class_data['name']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.configure(fg_color="#F8FAFC")
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text=class_data['name'], font=(self.FONT, 20, "bold"), text_color="#1E293B").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(header, text=class_data['semester'], font=(self.FONT, 14), text_color="#64748B").pack(side="left")
        
        # Chỉ CVHT mới có nút Import
        if api.user_info.get("role") == "CVHT":
            ctk.CTkButton(header, text="Import Students", fg_color="#10B981", hover_color="#059669",
                          command=lambda: self.import_students(class_data['_id'])).pack(side="right", padx=20)
        
        # Student List
        list_frame = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(list_frame, text="Students", font=(self.FONT, 16, "bold"), text_color="#334155").pack(pady=15, padx=20, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        loading = ctk.CTkLabel(scroll, text="Loading students...", text_color="gray")
        loading.pack(pady=20)
        
        def load_students():
            students = api.get_class_students(class_data['_id'])
            dialog.after(0, lambda: render_students(students, loading, scroll))
        
        def render_students(students, loading_lbl, container):
            loading_lbl.destroy()
            if not students:
                ctk.CTkLabel(container, text="No students in this class").pack(pady=20)
                return
            
            for student in students:
                row = ctk.CTkFrame(container, fg_color="#F8FAFC", corner_radius=8)
                row.pack(fill="x", pady=5)
                
                ctk.CTkLabel(row, text=f"👤 {student['full_name']}", font=(self.FONT, 13, "bold"), 
                             text_color="#1E293B", anchor="w").pack(side="left", padx=15, pady=10)
                ctk.CTkLabel(row, text=student['mssv'], font=(self.FONT, 12), 
                             text_color="#64748B").pack(side="left", padx=10)
                
                if api.user_info.get("role") == "CVHT":
                    ctk.CTkButton(row, text="Remove", width=80, fg_color="#EF4444", hover_color="#DC2626",
                                  command=lambda s=student: self.remove_student(class_data['_id'], s['mssv'], dialog)).pack(side="right", padx=10)
        
        threading.Thread(target=load_students).start()

    def import_students(self, class_id):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv")])
        if file_path:
            success, result = api.import_students(class_id, file_path)
            if success:
                msg = f"Imported {result.get('added_count', 0)} students"
                if result.get('errors'):
                    msg += f"\n\nErrors:\n" + "\n".join(result['errors'][:5])
                messagebox.showinfo("Import Result", msg)
                self.load()
            else:
                messagebox.showerror("Error", str(result))

    def remove_student(self, class_id, user_id, dialog):
        if messagebox.askyesno("Confirm", f"Remove student from class?"):
            success, msg = api.remove_student_from_class(class_id, user_id)
            if success:
                messagebox.showinfo("Success", "Student removed")
                dialog.destroy()
                self.load()
            else:
                messagebox.showerror("Error", msg)

    def popup_create(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Class")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        ctk.CTkLabel(dialog, text="Create New Class", font=(self.FONT, 18, "bold"), text_color="#333").pack(pady=20)
        
        ctk.CTkLabel(dialog, text="Class Name", font=(self.FONT, 13), text_color="#555").pack(anchor="w", padx=30)
        entry_name = ctk.CTkEntry(dialog, width=340, height=40)
        entry_name.pack(padx=30, pady=(5, 15))
        
        ctk.CTkLabel(dialog, text="Semester", font=(self.FONT, 13), text_color="#555").pack(anchor="w", padx=30)
        entry_sem = ctk.CTkEntry(dialog, width=340, height=40, placeholder_text="e.g., 2025-1")
        entry_sem.pack(padx=30, pady=(5, 20))
        
        def submit():
            name = entry_name.get()
            sem = entry_sem.get()
            if name and sem:
                success, msg = api.create_class(name, sem)
                if success:
                    messagebox.showinfo("Success", "Class created!")
                    dialog.destroy()
                    self.load()
                else:
                    messagebox.showerror("Error", msg)
        
        ctk.CTkButton(dialog, text="Create", width=340, height=45, command=submit).pack(padx=30)