import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox, filedialog

class ClassesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "DejaVu Sans"
        
        # Modern header with gradient
        self.create_header()
        
        # Grid layout for cards
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", 
                                            scrollbar_button_color="#CBD5E1")
        self.scroll.pack(fill="both", expand=True, pady=10)
        self.scroll.grid_columnconfigure((0,1,2), weight=1)
        
        # Loading state
        self.loading_frame = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=16,
                                         border_width=1, border_color="#E2E8F0")
        self.loading_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=20)
        
        ctk.CTkLabel(self.loading_frame, text="⏳", font=(self.FONT, 32)).pack(pady=(30, 10))
        ctk.CTkLabel(self.loading_frame, text="Loading your classes...", 
                    font=(self.FONT, 14), text_color="#64748B").pack(pady=(0, 30))
        
        threading.Thread(target=self.load).start()

    def create_header(self):
        """Modern header with actions"""
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=16, 
                             border_width=1, border_color="#E2E8F0")
        header.pack(fill="x", padx=15, pady=(0, 20))
        
        # Gradient accent
        ctk.CTkFrame(header, height=4, fg_color="#6366F1", corner_radius=16).pack(fill="x")
        
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="x", padx=25, pady=20)
        
        # Title with icon
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, text="🎓", font=(self.FONT, 28)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(title_frame, text="My Classes", font=(self.FONT, 24, "bold"), 
                    text_color="#1E293B").pack(side="left")
        
        # Action button for CVHT
        if api.user_info.get("role") == "CVHT":
            btn = ctk.CTkButton(content, text="+ Create New Class", 
                               font=(self.FONT, 14, "bold"),
                               fg_color="#6366F1", hover_color="#4F46E5",
                               corner_radius=10, height=40,
                               command=self.popup_create)
            btn.pack(side="right")

    def load(self):
        data = api.get_my_classes()
        self.after(0, lambda: self.render(data))

    def render(self, classes):
        self.loading_frame.destroy()
        
        if not classes:
            # Empty state
            empty = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=16,
                                border_width=1, border_color="#E2E8F0")
            empty.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=20)
            
            ctk.CTkLabel(empty, text="📚", font=(self.FONT, 48)).pack(pady=(40, 10))
            ctk.CTkLabel(empty, text="No classes found", 
                        font=(self.FONT, 18, "bold"), text_color="#64748B").pack()
            ctk.CTkLabel(empty, text="You haven't joined any classes yet", 
                        font=(self.FONT, 13), text_color="#94A3B8").pack(pady=(5, 40))
            return
        
        # Render class cards
        for i, c in enumerate(classes):
            self.create_class_card(c, i//3, i%3)

    def create_class_card(self, data, row, col):
        """Modern class card with hover effect"""
        card = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=16, 
                           border_width=1, border_color="#E2E8F0")
        card.grid(row=row, column=col, sticky="nsew", padx=12, pady=12)
        
        # Color accent based on semester
        colors = ["#6366F1", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981"]
        accent_color = colors[hash(data.get("name", "")) % len(colors)]
        
        accent = ctk.CTkFrame(card, height=6, fg_color=accent_color, corner_radius=16)
        accent.pack(fill="x")
        
        # Content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Class icon
        icon_frame = ctk.CTkFrame(content, width=50, height=50, corner_radius=25,
                                 fg_color=f"{accent_color}20")
        icon_frame.pack(anchor="w", pady=(0, 15))
        icon_frame.pack_propagate(False)
        
        ctk.CTkLabel(icon_frame, text="📖", font=(self.FONT, 24)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Class name
        ctk.CTkLabel(content, text=data.get("name", "Unnamed Class"), 
                    font=(self.FONT, 17, "bold"), text_color="#1E293B", 
                    anchor="w", wraplength=200).pack(fill="x", pady=(0, 5))
        
        # Semester badge
        semester_frame = ctk.CTkFrame(content, fg_color="transparent")
        semester_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(semester_frame, text="📅", font=(self.FONT, 12)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(semester_frame, text=data.get("semester", "N/A"), 
                    font=(self.FONT, 12), text_color="#64748B").pack(side="left")
        
        # Student count
        student_count = len(data.get('student_ids', []))
        count_frame = ctk.CTkFrame(content, fg_color="#F8FAFC", corner_radius=8)
        count_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(count_frame, text=f"👥 {student_count} students", 
                    font=(self.FONT, 12, "bold"), text_color="#475569").pack(pady=8)
        
        # Action button
        btn = ctk.CTkButton(content, text="View Details →", 
                           fg_color=accent_color, hover_color=accent_color,
                           text_color="white", corner_radius=10, height=38,
                           font=(self.FONT, 13, "bold"),
                           command=lambda d=data: self.open_class_detail(d))
        btn.pack(fill="x")

    def open_class_detail(self, class_data):
        """Modern class detail dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Class: {class_data['name']}")
        dialog.geometry("800x650")
        dialog.transient(self)
        dialog.configure(fg_color="#F8FAFC")
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="white", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkFrame(header, height=4, fg_color="#6366F1").pack(fill="x")
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=30, pady=20)
        
        # Class info
        info_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        info_frame.pack(side="left")
        
        ctk.CTkLabel(info_frame, text=class_data['name'], 
                    font=(self.FONT, 22, "bold"), text_color="#1E293B").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"📅 {class_data['semester']}", 
                    font=(self.FONT, 13), text_color="#64748B").pack(anchor="w", pady=(5, 0))
        
        # Actions for CVHT
        if api.user_info.get("role") == "CVHT":
            action_frame = ctk.CTkFrame(header_content, fg_color="transparent")
            action_frame.pack(side="right")
            
            ctk.CTkButton(action_frame, text="📥 Import Students", 
                         fg_color="#10B981", hover_color="#059669",
                         corner_radius=10, height=38,
                         command=lambda: self.import_students(class_data['_id'])).pack()
        
        # Student list container
        list_container = ctk.CTkFrame(dialog, fg_color="white", corner_radius=16,
                                     border_width=1, border_color="#E2E8F0")
        list_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # List header
        list_header = ctk.CTkFrame(list_container, fg_color="transparent")
        list_header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(list_header, text="👥 Students", 
                    font=(self.FONT, 18, "bold"), text_color="#1E293B").pack(side="left")
        
        # Scrollable student list
        scroll = ctk.CTkScrollableFrame(list_container, fg_color="transparent",
                                       scrollbar_button_color="#CBD5E1")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        loading = ctk.CTkLabel(scroll, text="Loading students...", text_color="#94A3B8")
        loading.pack(pady=30)
        
        def load_students():
            students = api.get_class_students(class_data['_id'])
            dialog.after(0, lambda: render_students(students, loading, scroll))
        
        def render_students(students, loading_lbl, container):
            loading_lbl.destroy()
            
            if not students:
                empty = ctk.CTkFrame(container, fg_color="#F8FAFC", corner_radius=12)
                empty.pack(fill="x", pady=20)
                ctk.CTkLabel(empty, text="No students in this class yet", 
                            font=(self.FONT, 13), text_color="#94A3B8").pack(pady=30)
                return
            
            for idx, student in enumerate(students):
                # Student row
                row = ctk.CTkFrame(container, fg_color="#F8FAFC" if idx % 2 == 0 else "white", 
                                  corner_radius=10)
                row.pack(fill="x", pady=3)
                
                # Avatar
                avatar = ctk.CTkFrame(row, width=40, height=40, corner_radius=20,
                                     fg_color="#E0F2FE", border_width=2, border_color="#3B82F6")
                avatar.pack(side="left", padx=15, pady=10)
                avatar.pack_propagate(False)
                
                initial = student['full_name'][0].upper() if student.get('full_name') else "?"
                ctk.CTkLabel(avatar, text=initial, font=(self.FONT, 16, "bold"), 
                            text_color="#0284C7").place(relx=0.5, rely=0.5, anchor="center")
                
                # Info
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, pady=10)
                
                ctk.CTkLabel(info, text=student.get('full_name', 'N/A'), 
                            font=(self.FONT, 14, "bold"), text_color="#1E293B", 
                            anchor="w").pack(anchor="w")
                
                detail_frame = ctk.CTkFrame(info, fg_color="transparent")
                detail_frame.pack(anchor="w")
                
                ctk.CTkLabel(detail_frame, text=f"🆔 {student['mssv']}", 
                            font=(self.FONT, 11), text_color="#64748B").pack(side="left", padx=(0, 15))
                ctk.CTkLabel(detail_frame, text=f"📧 {student['email']}", 
                            font=(self.FONT, 11), text_color="#64748B").pack(side="left")
                
                # Remove button for CVHT
                if api.user_info.get("role") == "CVHT":
                    ctk.CTkButton(row, text="✕", width=35, height=35,
                                 fg_color="#FEE2E2", hover_color="#FEF2F2",
                                 text_color="#DC2626", corner_radius=8,
                                 font=(self.FONT, 16, "bold"),
                                 command=lambda s=student: self.remove_student(class_data['_id'], s['_id'], dialog)).pack(side="right", padx=15)
        
        threading.Thread(target=load_students).start()

    def import_students(self, class_id):
        file_path = filedialog.askopenfilename(
            title="Select Student List",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv")]
        )
        if file_path:
            success, result = api.import_students(class_id, file_path)
            if success:
                msg = f"✅ Successfully imported {result.get('added_count', 0)} students"
                if result.get('errors'):
                    msg += f"\n\n⚠️ Errors:\n" + "\n".join(result['errors'][:5])
                messagebox.showinfo("Import Complete", msg)
                self.load()
            else:
                messagebox.showerror("Import Failed", str(result))

    def remove_student(self, class_id, user_id, dialog):
        if messagebox.askyesno("Confirm Removal", "Remove this student from the class?"):
            success, msg = api.remove_student_from_class(class_id, user_id)
            if success:
                messagebox.showinfo("Success", "Student removed successfully")
                dialog.destroy()
                self.load()
            else:
                messagebox.showerror("Error", msg)

    def popup_create(self):
        """Modern create class dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Class")
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="#6366F1", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="🎓 Create New Class", 
                    font=(self.FONT, 20, "bold"), text_color="white").pack(pady=25)
        
        # Form
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Class name
        ctk.CTkLabel(form, text="Class Name", font=(self.FONT, 13, "bold"), 
                    text_color="#1E293B").pack(anchor="w", pady=(0, 8))
        entry_name = ctk.CTkEntry(form, height=45, font=(self.FONT, 13),
                                 placeholder_text="e.g., Advanced Programming",
                                 border_color="#E2E8F0", fg_color="#F8FAFC")
        entry_name.pack(fill="x", pady=(0, 20))
        
        # Semester
        ctk.CTkLabel(form, text="Semester", font=(self.FONT, 13, "bold"), 
                    text_color="#1E293B").pack(anchor="w", pady=(0, 8))
        entry_sem = ctk.CTkEntry(form, height=45, font=(self.FONT, 13),
                                placeholder_text="e.g., 2025-1",
                                border_color="#E2E8F0", fg_color="#F8FAFC")
        entry_sem.pack(fill="x", pady=(0, 30))
        
        def submit():
            name = entry_name.get().strip()
            sem = entry_sem.get().strip()
            
            if not name or not sem:
                messagebox.showwarning("Missing Information", "Please fill in all fields")
                return
            
            success, msg = api.create_class(name, sem)
            if success:
                messagebox.showinfo("Success", "✅ Class created successfully!")
                dialog.destroy()
                self.load()
            else:
                messagebox.showerror("Error", f"Failed to create class: {msg}")
        
        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="Cancel", height=45,
                     fg_color="#F1F5F9", hover_color="#E2E8F0",
                     text_color="#64748B", corner_radius=10,
                     command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Create Class", height=45,
                     fg_color="#6366F1", hover_color="#4F46E5",
                     corner_radius=10, font=(self.FONT, 14, "bold"),
                     command=submit).pack(side="right", fill="x", expand=True)
