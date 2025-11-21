import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image
import os

class ClassesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent", 
                         scrollbar_button_color="#F1F5F9", scrollbar_button_hover_color="#94A3B8")
        self.FONT = "Ubuntu"
        self.role = api.user_info.get("role")
        
        # --- LOAD ICONS TỪ FILE ẢNH ---
        self.icons = {}
        self.load_icons()

        # Cấu hình Grid: 3 cột giãn đều
        self.grid_columnconfigure((0,1,2), weight=1)
        
        # --- HEADER ---
        self.create_header()

        # --- LOADING AREA ---
        self.loading = ctk.CTkLabel(self, text="Loading classes...", text_color="gray", font=(self.FONT, 14))
        self.loading.grid(row=1, column=1, pady=50)
        
        # Bắt đầu tải dữ liệu
        threading.Thread(target=self.load, daemon=True).start()

    def load_icons(self):
        """Hàm load ảnh PNG để thay thế Emoji"""
        icon_names = {
            "cal": "calendar.png",
            "group": "group.png",
            "arrow": "arrow_right.png",
            "plus": "plus.png",
            "import": "import.png",
            "trash": "delete.png",
            "grade": "grade.png",
            "forum": "forum.png"
        }
        # Đường dẫn tương đối từ file này ra thư mục assets
        base_path = os.path.join(os.path.dirname(__file__), "../../assets/icons")
        
        for key, filename in icon_names.items():
            try:
                path = os.path.join(base_path, filename)
                self.icons[key] = ctk.CTkImage(Image.open(path), size=(20, 20))
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")
                self.icons[key] = None

    def create_header(self):
        top = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        top.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 20))
        
        # Tiêu đề
        ctk.CTkLabel(top, text="My Classes", font=(self.FONT, 24, "bold"), 
                     text_color="#334155").pack(side="left", padx=25, pady=15)
        
        # Nút Tạo lớp (Chỉ CVHT)
        if self.role == "CVHT":
            ctk.CTkButton(top, text="  Create New Class", 
                          image=self.icons.get('plus'), compound="left",
                          fg_color="#3B82F6", hover_color="#2563EB",
                          font=(self.FONT, 14, "bold"), width=160, height=40,
                          command=self.popup_create).pack(side="right", padx=20)

    def refresh(self):
        # Xóa các thẻ cũ (giữ lại header ở row 0)
        for widget in self.winfo_children():
            try:
                if int(widget.grid_info().get("row", 0)) >= 1:
                    widget.destroy()
            except: pass
        
        self.loading = ctk.CTkLabel(self, text="Refreshing...", text_color="gray")
        self.loading.grid(row=1, column=1, pady=50)
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        # Lấy tất cả lớp (không lọc)
        data = api.get_my_classes() 
        self.after(0, lambda: self.render(data))

    def render(self, classes):
        try: self.loading.destroy()
        except: pass

        if not classes:
            ctk.CTkLabel(self, text="No classes found.", font=(self.FONT, 16)).grid(row=1, column=1)
            return
        
        # Render lưới 3 cột
        for i, c in enumerate(classes):
            self.card(c, (i//3) + 1, i%3)

    def card(self, data, r, c):
        # --- CARD DESIGN ---
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=16, border_width=1, border_color="#E2E8F0")
        f.grid(row=r, column=c, sticky="nsew", padx=12, pady=12)
        
        # Header màu xanh cố định
        ctk.CTkFrame(f, height=6, fg_color="#3B82F6", corner_radius=6).pack(fill="x")
        
        # Nội dung
        box = ctk.CTkFrame(f, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tên Lớp - xử lý cả 2 loại
        if 'name' in data:
            class_name = data['name']
        else:
            # Ưu tiên class_code, fallback về group
            class_name = f"{data.get('semester', 'N/A')} - {data.get('class_code', data.get('group', 'N/A'))}"
        
        ctk.CTkLabel(box, text=class_name, font=(self.FONT, 18, "bold"), 
                     text_color="#1E293B", anchor="w", wraplength=200).pack(fill="x")
        
        # Info Row (Semester & Count)
        info_box = ctk.CTkFrame(box, fg_color="transparent")
        info_box.pack(fill="x", pady=(15, 5))
        
        # Semester (Dùng Icon Ảnh)
        row1 = ctk.CTkFrame(info_box, fg_color="transparent")
        row1.pack(anchor="w")
        ctk.CTkLabel(row1, text="", image=self.icons.get('cal'), width=20).pack(side="left")
        semester_text = data.get('semester', data.get('academic_year', 'N/A'))
        ctk.CTkLabel(row1, text=f"  {semester_text}", font=(self.FONT, 13), text_color="#64748B").pack(side="left")

        # Student Count (Dùng Icon Ảnh)
        row2 = ctk.CTkFrame(info_box, fg_color="transparent")
        row2.pack(anchor="w", pady=(8, 0))
        count = len(data.get('student_ids', []))
        ctk.CTkLabel(row2, text="", image=self.icons.get('group'), width=20).pack(side="left")
        ctk.CTkLabel(row2, text=f"  {count} Students", font=(self.FONT, 13), text_color="#64748B").pack(side="left")
        
        # Button Action
        btn_text = "Manage Class" if self.role == "CVHT" or self.role == "TEACHER" else "Enter Class"
        
        btn = ctk.CTkButton(f, text=f"{btn_text}  ", image=self.icons.get('arrow'), compound="right",
                            fg_color="#F1F5F9", text_color="#334155", hover_color="#E2E8F0",
                            font=(self.FONT, 13, "bold"), height=45, corner_radius=10,
                            command=lambda: self.open_detail(data))
        btn.pack(fill="x", padx=20, pady=(0, 20))

    def open_detail(self, data):
        # Mở cửa sổ chi tiết (Truyền dict icons sang để không phải load lại)
        ClassDetailDialog(self, data, self.role, self.icons)

    def popup_create(self):
        if self.role == "CVHT":
            name = simpledialog.askstring("Create Class", "Class Name (e.g., CNTT-K17):")
            year = simpledialog.askstring("Create Class", "Academic Year (e.g., 2020-2024):")
            if name and year:
                ok, msg = api.create_administrative_class(name, year)
                if ok: self.refresh()
                else: messagebox.showerror("Error", msg)
        elif self.role == "TEACHER":
            messagebox.showinfo("Info", "Please use 'My Courses' menu to create course classes")
        else:
            messagebox.showinfo("Info", "You don't have permission to create classes")


# --- CLASS DETAIL DIALOG (GIAO DIỆN TABBED) ---
class ClassDetailDialog(ctk.CTkToplevel):
    def __init__(self, parent, class_data, role, icons):
        super().__init__(parent)
        self.data = class_data
        self.role = role
        self.icons = icons
        
        self.title(f"Class: {class_data['name']}")
        self.geometry("900x650")
        self.configure(fg_color="#F8FAFC") # Nền xám nhạt
        self.FONT = "Ubuntu"

        # HEADER (Đẹp hơn)
        self.create_header()

        # TAB VIEW (Chia nội dung Overview / Student List)
        self.tabs = ctk.CTkTabview(self, width=850, height=500, fg_color="transparent",
                                   segmented_button_selected_color="#3B82F6",
                                   segmented_button_unselected_color="white",
                                   text_color_disabled="gray",
                                   text_color="black") 
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tabs.add("Overview")
        self.tabs.add("Student List")
        
        self.setup_overview_tab()
        self.setup_student_tab()

    def create_header(self):
        header = ctk.CTkFrame(self, height=100, fg_color="white", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkFrame(header, height=4, fg_color="#3B82F6").pack(fill="x") # Thanh màu xanh
        
        h_content = ctk.CTkFrame(header, fg_color="transparent")
        h_content.pack(fill="x", padx=30, pady=25)
        
        # Icon lớp học to (Giả lập bằng Frame tròn nếu ko có ảnh)
        icon_bg = ctk.CTkFrame(h_content, width=60, height=60, corner_radius=30, fg_color="#E0F2FE")
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        
        # Xử lý tên lớp
        if 'name' in self.data:
            class_name = self.data['name']
            initial = class_name[0]
        else:
            # Ưu tiên class_code, fallback về group
            display_code = self.data.get('class_code', self.data.get('group', 'N/A'))
            class_name = f"{self.data.get('semester', 'N/A')} - {display_code}"
            initial = self.data.get('semester', 'C')[0]
        
        ctk.CTkLabel(icon_bg, text=initial, font=(self.FONT, 30, "bold"), text_color="#3B82F6").place(relx=0.5, rely=0.5, anchor="center")

        # Thông tin text
        info = ctk.CTkFrame(h_content, fg_color="transparent")
        info.pack(side="left", padx=20)
        
        ctk.CTkLabel(info, text=class_name, font=(self.FONT, 26, "bold"), text_color="#1E293B").pack(anchor="w")
        
        # Sub text
        if 'semester' in self.data:
            sub_text = f"Semester: {self.data['semester']}  |  ID: {self.data.get('id', self.data.get('_id', 'N/A'))}"
        else:
            sub_text = f"Year: {self.data.get('academic_year', 'N/A')}  |  ID: {self.data.get('id', self.data.get('_id', 'N/A'))}"
        
        ctk.CTkLabel(info, text=sub_text, font=(self.FONT, 13), text_color="#64748B").pack(anchor="w", pady=(5,0))

    def setup_overview_tab(self):
        tab = self.tabs.tab("Overview")
        
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=20, pady=20)
        grid.grid_columnconfigure((0, 1), weight=1)

        # Shortcut Buttons (Dùng ảnh)
        self.create_shortcut(grid, 0, 0, "Grade Board", "View & Manage Grades", 
                             self.icons.get('grade'),
                             lambda: messagebox.showinfo("Info", "Please use Grade Board in Sidebar"))

        self.create_shortcut(grid, 0, 1, "Class Forum", "Discussion & News", 
                             self.icons.get('forum'),
                             lambda: messagebox.showinfo("Info", "Please use Forum in Sidebar"))

        # Quick Actions cho CVHT
        if self.role == "CVHT":
            action_frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
            action_frame.pack(fill="x", padx=20, pady=20)
            ctk.CTkLabel(action_frame, text="Teacher Actions", font=(self.FONT, 14, "bold"), text_color="gray").pack(anchor="w", padx=20, pady=10)
            
            ctk.CTkButton(action_frame, text="  Import Students via Excel", 
                          image=self.icons.get('import'), compound="left",
                          fg_color="#10B981", hover_color="#059669", height=45,
                          font=(self.FONT, 14, "bold"),
                          command=lambda: self.import_sv(self.data['_id'])).pack(fill="x", padx=20, pady=(0, 20))

    def create_shortcut(self, parent, r, c, title, desc, icon, cmd):
        btn = ctk.CTkButton(parent, text="", fg_color="white", hover_color="#F8FAFC",
                            corner_radius=16, border_width=1, border_color="#E2E8F0",
                            width=300, height=120, command=cmd)
        btn.grid(row=r, column=c, padx=15, pady=15, sticky="ew")
        
        content = ctk.CTkFrame(btn, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")
        
        if icon:
            ctk.CTkLabel(content, text="", image=icon).pack(pady=(0, 5))
        
        l1 = ctk.CTkLabel(content, text=title, font=(self.FONT, 18, "bold"), text_color="#334155")
        l1.pack()
        l2 = ctk.CTkLabel(content, text=desc, font=(self.FONT, 12), text_color="gray")
        l2.pack()
        
        # Bind click cho các label con để vẫn bấm được nút
        for w in [content, l1, l2]:
            w.bind("<Button-1>", lambda e: cmd())

    def setup_student_tab(self):
        tab = self.tabs.tab("Student List")
        
        # List Header
        header = ctk.CTkFrame(tab, fg_color="#E2E8F0", height=40, corner_radius=8)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="Info", font=(self.FONT, 12, "bold"), text_color="#475569", width=200).pack(side="left", padx=10)
        ctk.CTkLabel(header, text="MSSV", font=(self.FONT, 12, "bold"), text_color="#475569", width=100).pack(side="left")
        ctk.CTkLabel(header, text="Email", font=(self.FONT, 12, "bold"), text_color="#475569", width=200).pack(side="left")

        # Scroll List
        self.scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=5)
        
        self.load_students()

    def load_students(self):
        for w in self.scroll.winfo_children(): w.destroy()
        
        def fetch():
            sv = api.get_class_students(self.data['_id'])
            self.after(0, lambda: self.render_students(sv))
        
        threading.Thread(target=fetch, daemon=True).start()

    def render_students(self, students):
        if not students:
            ctk.CTkLabel(self.scroll, text="No students enrolled", text_color="gray").pack(pady=30)
            return
        
        for idx, s in enumerate(students):
            # Zebra striping (màu xen kẽ)
            bg_col = "white" if idx % 2 == 0 else "#F8FAFC"
            
            row = ctk.CTkFrame(self.scroll, fg_color=bg_col, corner_radius=8)
            row.pack(fill="x", pady=2)
            
            # Avatar + Name
            info_box = ctk.CTkFrame(row, fg_color="transparent", width=200)
            info_box.pack(side="left", padx=10)
            info_box.pack_propagate(False)
            
            initial = s.get('full_name', '?')[0].upper()
            av = ctk.CTkFrame(info_box, width=32, height=32, corner_radius=16, fg_color="#DBEAFE")
            av.pack(side="left")
            ctk.CTkLabel(av, text=initial, font=(self.FONT, 12, "bold"), text_color="#1D4ED8").place(relx=0.5, rely=0.5, anchor="center")
            
            ctk.CTkLabel(info_box, text=s.get('full_name', 'N/A'), font=(self.FONT, 13, "bold"), text_color="#334155").pack(side="left", padx=10)

            # MSSV
            ctk.CTkLabel(row, text=s['mssv'], font=(self.FONT, 13), width=100, anchor="w", text_color="#333").pack(side="left")
            
            # Email
            ctk.CTkLabel(row, text=s.get('email', ''), font=(self.FONT, 13), width=200, anchor="w", text_color="#333").pack(side="left")
            
            # Kick Button (CVHT)
            if self.role == "CVHT":
                ctk.CTkButton(row, text="", image=self.icons.get('trash'), width=30, height=30,
                              fg_color="transparent", hover_color="#FEE2E2",
                              command=lambda uid=s['_id']: self.kick(uid)).pack(side="right", padx=10)

    def import_sv(self, cid):
        path = filedialog.askopenfilename()
        if path:
            ok, res = api.import_students(cid, path)
            if ok:
                messagebox.showinfo("Success", f"Added {res.get('added_count', 0)} students")
                self.load_students()
            else:
                messagebox.showerror("Error", str(res))

    def kick(self, uid):
        if messagebox.askyesno("Confirm", "Remove student from class?"):
            if api.remove_student(self.data['_id'], uid):
                messagebox.showinfo("Done", "Student removed")
                # Reload class data to update student count
                updated_class = api.get_class_detail(self.data['_id'])
                if updated_class:
                    self.data = updated_class
                    # Update header with new count
                    self.create_header()
                self.load_students()
            else:
                messagebox.showerror("Error", "Failed to remove")