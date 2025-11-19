import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox

class ClassesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Font
        self.FONT_FAMILY = "DejaVu Sans"

        # --- 1. HEADER (Tiêu đề + Nút Tạo lớp) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))

        self.lbl_title = ctk.CTkLabel(self.header_frame, text="My Classes", 
                                      font=(self.FONT_FAMILY, 24, "bold"), text_color="#334155")
        self.lbl_title.pack(side="left")

        # Chỉ hiện nút "Create Class" nếu là CVHT
        user_role = api.user_info.get("role", "STUDENT")
        if user_role == "CVHT":
            self.btn_create = ctk.CTkButton(self.header_frame, text="+ Create Class", 
                                            font=(self.FONT_FAMILY, 14, "bold"),
                                            fg_color="#3B82F6", hover_color="#2563EB",
                                            height=40, corner_radius=8,
                                            command=self.open_create_dialog)
            self.btn_create.pack(side="right")

        # --- 2. CONTENT AREA (Scrollable Grid) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Cấu hình Grid cho các thẻ (3 cột)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        self.scroll_frame.grid_columnconfigure(2, weight=1)

        self.loading_lbl = ctk.CTkLabel(self.scroll_frame, text="Loading classes...", text_color="gray")
        self.loading_lbl.grid(row=0, column=1, pady=20)

        # Load data
        threading.Thread(target=self.load_classes).start()

    def load_classes(self):
        classes = api.get_my_classes()
        self.after(0, lambda: self.render_classes(classes))

    def render_classes(self, classes):
        self.loading_lbl.destroy()
        
        if not classes:
            ctk.CTkLabel(self.scroll_frame, text="No classes found.", 
                         font=(self.FONT_FAMILY, 16)).grid(row=0, column=1, pady=20)
            return

        # Render từng thẻ
        for i, class_data in enumerate(classes):
            row = i // 3
            col = i % 3
            self.create_class_card(class_data, row, col)

    def create_class_card(self, data, row, col):
        """Tạo giao diện 1 thẻ lớp học"""
        card = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=15, 
                            border_width=1, border_color="#E2E8F0")
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        
        # Header màu của thẻ
        header_color = "#6366F1" # Màu tím indigo
        header = ctk.CTkFrame(card, height=8, fg_color=header_color, corner_radius=15)
        header.pack(fill="x")
        # Hack để che bo góc dưới của header cho phẳng
        ctk.CTkFrame(card, height=5, fg_color="white").pack(fill="x") 

        # Nội dung thẻ
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)

        # Tên lớp
        class_name = data.get("name", "Unknown Class")
        ctk.CTkLabel(content, text=class_name, anchor="w",
                     font=(self.FONT_FAMILY, 16, "bold"), text_color="#1E293B").pack(fill="x")

        # Học kỳ
        semester = data.get("semester", "N/A")
        ctk.CTkLabel(content, text=f"Semester: {semester}", anchor="w",
                     font=(self.FONT_FAMILY, 12), text_color="#64748B").pack(fill="x", pady=(5, 0))

        # Sĩ số
        count = len(data.get("student_ids", []))
        ctk.CTkLabel(content, text=f"{count} Students", anchor="w",
                     font=(self.FONT_FAMILY, 12, "bold"), text_color="#6366F1").pack(fill="x", pady=(15, 0))

        # Nút Vào lớp
        btn_enter = ctk.CTkButton(card, text="Go to Class ->", 
                                  fg_color="#F1F5F9", text_color="#334155", hover_color="#E2E8F0",
                                  height=35, font=(self.FONT_FAMILY, 13, "bold"),
                                  command=lambda id=data.get("_id"): self.open_class_detail(id))
        btn_enter.pack(fill="x", padx=15, pady=(10, 15))

    def open_class_detail(self, class_id):
        print(f"Open class: {class_id}")
        # TODO: Chuyển hướng sang màn hình chi tiết lớp (Sẽ làm ở phần sau)
        messagebox.showinfo("Info", f"Opening class ID: {class_id}\n(Tính năng chi tiết lớp sẽ làm ở bước sau)")

    # --- POPUP TẠO LỚP MỚI ---
    def open_create_dialog(self):
        dialog = CreateClassDialog(self)
        self.wait_window(dialog) # Chờ đóng cửa sổ thì refresh lại list
        self.load_classes() # Reload lại danh sách

# Class cửa sổ popup tạo lớp
class CreateClassDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create New Class")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Cho popup nổi lên trên và chặn tương tác cửa sổ chính (Modal)
        self.transient(parent)
        self.grab_set()
        
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="Create New Class", font=("DejaVu Sans", 20, "bold"), text_color="#333").pack(pady=20)

        self.entry_name = ctk.CTkEntry(self, placeholder_text="Class Name (e.g. Python Basic)", width=300, height=40)
        self.entry_name.pack(pady=10)

        self.entry_sem = ctk.CTkEntry(self, placeholder_text="Semester (e.g. 2025-1)", width=300, height=40)
        self.entry_sem.pack(pady=10)

        self.btn_save = ctk.CTkButton(self, text="Create Now", width=300, height=45,
                                      fg_color="#3B82F6", hover_color="#2563EB",
                                      command=self.on_save)
        self.btn_save.pack(pady=20)

    def on_save(self):
        name = self.entry_name.get()
        sem = self.entry_sem.get()
        
        if not name or not sem:
            return

        self.btn_save.configure(state="disabled", text="Creating...")
        
        # Gọi API
        success, msg = api.create_class(name, sem)
        
        if success:
            self.destroy() # Đóng popup
        else:
            self.btn_save.configure(state="normal", text="Create Now")
            messagebox.showerror("Error", msg)