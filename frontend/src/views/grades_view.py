import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import filedialog, messagebox
import os

class GradesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT_FAMILY = "DejaVu Sans"

        # --- 1. HEADER (Bộ lọc & Tool) ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))

        # Tiêu đề
        self.lbl_title = ctk.CTkLabel(self.header, text="Grade Board", 
                                      font=(self.FONT_FAMILY, 24, "bold"), text_color="#334155")
        self.lbl_title.pack(side="left")

        # Controls Frame (Chứa các nút lọc)
        self.controls = ctk.CTkFrame(self.header, fg_color="transparent")
        self.controls.pack(side="right")

        # Combobox chọn kỳ học
        self.sem_var = ctk.StringVar(value="2025-1")
        self.cb_semester = ctk.CTkComboBox(self.controls, values=["2024-1", "2024-2", "2025-1"],
                                           width=120, font=(self.FONT_FAMILY, 13),
                                           variable=self.sem_var, command=self.refresh_data)
        self.cb_semester.pack(side="left", padx=10)

        # Logic Phân quyền: Nếu là CVHT thì hiện thêm chọn Lớp và nút Import
        self.user_role = api.user_info.get("role", "STUDENT")
        self.selected_class_id = None

        if self.user_role == "CVHT":
            # Combobox chọn lớp
            self.class_map = {} # Lưu {Tên lớp: ID}
            self.cb_class = ctk.CTkComboBox(self.controls, values=["Loading..."], width=180,
                                            font=(self.FONT_FAMILY, 13), command=self.on_class_change)
            self.cb_class.pack(side="left", padx=10)
            
            # Nút Import
            self.btn_import = ctk.CTkButton(self.controls, text="Import Excel",
                                            fg_color="#10B981", hover_color="#059669",
                                            font=(self.FONT_FAMILY, 13, "bold"), width=120,
                                            command=self.open_import_dialog)
            self.btn_import.pack(side="left", padx=10)

            # Load danh sách lớp ngay khi mở
            threading.Thread(target=self.load_classes_for_combobox).start()

        # Nút Refresh
        self.btn_refresh = ctk.CTkButton(self.controls, text="↻", width=40,
                                         fg_color="#94A3B8", hover_color="#64748B",
                                         command=lambda: self.refresh_data(None))
        self.btn_refresh.pack(side="left")

        # --- 2. TABLE AREA ---
        # Header bảng
        self.table_header = ctk.CTkFrame(self, height=40, fg_color="#E2E8F0", corner_radius=5)
        self.table_header.pack(fill="x", pady=(10, 0))
        self.create_table_columns(self.table_header, is_header=True)

        # Nội dung bảng (Scrollable)
        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=5)
        self.table_scroll.pack(fill="both", expand=True, pady=(5, 0))

        # Load dữ liệu lần đầu (Nếu là SV)
        if self.user_role == "STUDENT":
            self.refresh_data(None)

    def create_table_columns(self, master, is_header=False):
        """Hàm vẽ cột cho bảng"""
        font = (self.FONT_FAMILY, 13, "bold") if is_header else (self.FONT_FAMILY, 13)
        text_color = "#1E293B" if is_header else "#334155"
        
        # Định nghĩa cột: (Tên, Width weight)
        columns = [("Semester", 1), ("GPA (4)", 1), ("Credits", 1), ("Debt", 1), ("Warning", 1)]
        
        if self.user_role == "CVHT":
            # CVHT cần xem MSSV
            columns.insert(0, ("Student ID", 2))

        for idx, (col_name, weight) in enumerate(columns):
            lbl = ctk.CTkLabel(master, text=col_name, font=font, text_color=text_color)
            lbl.pack(side="left", fill="x", expand=True, padx=5)

    def add_row(self, data):
        """Thêm 1 dòng vào bảng"""
        row = ctk.CTkFrame(self.table_scroll, height=40, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # Dữ liệu hiển thị
        # Nếu là CVHT thì cột đầu là student_id, SV thì không có
        values = []
        if self.user_role == "CVHT":
            values.append(data.get("student_id", "N/A"))
            
        values.extend([
            data.get("semester", ""),
            str(data.get("gpa", 0.0)),
            str(data.get("credits_earned", 0)),
            "Yes" if data.get("tuition_debt") else "No",
            "Level " + str(data.get("academic_warning", 0))
        ])
        
        font = (self.FONT_FAMILY, 13)
        
        for i, val in enumerate(values):
            # Tô màu cảnh báo
            color = "#334155"
            if i == len(values)-2 and val == "Yes": color = "#EF4444" # Nợ phí -> Đỏ
            if i == len(values)-1 and val != "Level 0": color = "#F59E0B" # Cảnh báo -> Cam

            lbl = ctk.CTkLabel(row, text=val, font=font, text_color=color)
            lbl.pack(side="left", fill="x", expand=True, padx=5)
            
        # Kẻ đường gạch ngang mờ
        ctk.CTkFrame(self.table_scroll, height=1, fg_color="#F1F5F9").pack(fill="x")

    def load_classes_for_combobox(self):
        """Lấy danh sách lớp để CVHT chọn"""
        classes = api.get_my_classes() # API trả về list dict
        if classes:
            self.class_map = {c['name']: c['_id'] for c in classes}
            class_names = list(self.class_map.keys())
            self.cb_class.configure(values=class_names)
            if class_names:
                self.cb_class.set(class_names[0])
                self.selected_class_id = self.class_map[class_names[0]]
                # Load dữ liệu lớp đầu tiên luôn
                self.refresh_data(None)

    def on_class_change(self, choice):
        self.selected_class_id = self.class_map.get(choice)
        self.refresh_data(None)

    def refresh_data(self, _):
        # Xóa dữ liệu cũ
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
            
        sem = self.sem_var.get()
        
        threading.Thread(target=lambda: self.fetch_grades(sem)).start()

    def fetch_grades(self, semester):
        data = []
        if self.user_role == "STUDENT":
            data = api.get_my_grades(semester)
        elif self.user_role == "CVHT" and self.selected_class_id:
            data = api.get_class_grades(self.selected_class_id, semester)
            
        self.after(0, lambda: self.render_table(data))

    def render_table(self, data):
        if not data:
            ctk.CTkLabel(self.table_scroll, text="No data found for this semester.", text_color="gray").pack(pady=20)
            return
            
        for record in data:
            self.add_row(record)

    def open_import_dialog(self):
        if not self.selected_class_id:
            messagebox.showwarning("Warning", "Please select a class first.")
            return
            
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if file_path:
            # Hiện loading
            self.btn_import.configure(state="disabled", text="Uploading...")
            sem = self.sem_var.get()
            
            threading.Thread(target=lambda: self.run_import(self.selected_class_id, sem, file_path)).start()

    def run_import(self, class_id, sem, file_path):
        success, res = api.import_grades(class_id, sem, file_path)
        self.after(0, lambda: self.post_import(success, res))

    def post_import(self, success, res):
        self.btn_import.configure(state="normal", text="Import Excel")
        if success:
            msg = f"Success! Imported {res.get('success_count')} records."
            if res.get('errors'):
                msg += f"\nErrors:\n" + "\n".join(res['errors'][:5])
            messagebox.showinfo("Import Result", msg)
            self.refresh_data(None) # Reload bảng
        else:
            messagebox.showerror("Error", str(res))