import customtkinter as ctk
from tkinter import messagebox
from src.api.client import api

class CourseGradesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.selected_class = None
        self.grade_entries = {}  # Store entry widgets for grades
        self.students_data = []  # Store student data
        self.build_ui()
        self.load_classes()

    def build_ui(self):
        # Header with save button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Nhập điểm", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(side="left")
        
        self.save_btn = ctk.CTkButton(header_frame, text="💾 Lưu điểm", font=self.FONT_NORMAL,
                                     height=36, fg_color="#0EA5E9", hover_color="#0284C7",
                                     command=self.save_grades, state="disabled")
        self.save_btn.pack(side="right")
        
        # Instructions
        info = ctk.CTkFrame(self, fg_color="#EFF6FF", corner_radius=8, border_width=1, border_color="#BFDBFE")
        info.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(info, text="Chọn lớp học phần và nhập điểm trực tiếp cho từng sinh viên. Điểm tổng kết sẽ được tính tự động.",
                    font=self.FONT_NORMAL, text_color="#1E40AF").pack(padx=20, pady=15)
        
        # Class selector with formula display
        selector_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        selector_frame.pack(fill="x", pady=(0, 20))
        
        inner = ctk.CTkFrame(selector_frame, fg_color="transparent")
        inner.pack(padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="Chọn lớp học phần:", font=self.FONT_NORMAL,
                    text_color="#334155").pack(side="left", padx=(0, 15))
        
        self.class_var = ctk.StringVar(value="Chọn một lớp...")
        self.class_menu = ctk.CTkOptionMenu(inner, variable=self.class_var, values=["Đang tải..."],
                                            font=self.FONT_NORMAL, width=400,
                                            command=self.on_class_selected)
        self.class_menu.pack(side="left", padx=(0, 15))
        
        # Grade formula info
        self.formula_label = ctk.CTkLabel(inner, text="", font=self.FONT_SMALL, text_color="#64748B")
        self.formula_label.pack(side="left", padx=(15, 0))
        
        # Grades table
        self.table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table_content = ctk.CTkScrollableFrame(self.table_frame, fg_color="transparent")
        self.table_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.table_content, text="Chọn một lớp để bắt đầu nhập điểm",
                    font=self.FONT_NORMAL, text_color="#94A3B8").pack(expand=True)

    def load_classes(self):
        """Load danh sách lớp học phần"""
        classes = api.get_my_course_classes()
        
        if not classes:
            self.class_menu.configure(values=["Không có lớp nào"])
            return
        
        self.classes_data = classes
        # Display: Course Name - Class Code
        class_names = []
        for c in classes:
            course_name = c.get('course_name', 'Unknown')
            class_code = c.get('class_code', 'N/A')
            class_names.append(f"{course_name} - {class_code}")
        
        self.class_menu.configure(values=class_names)
        if class_names:
            self.class_var.set(class_names[0])
            self.on_class_selected(class_names[0])

    def on_class_selected(self, selection):
        """Khi chọn lớp"""
        if not hasattr(self, 'classes_data'):
            return
        
        for cls in self.classes_data:
            course_name = cls.get('course_name', 'Unknown')
            class_code = cls.get('class_code', 'N/A')
            display_name = f"{course_name} - {class_code}"
            
            if display_name == selection:
                self.selected_class = cls
                # Update formula info
                formula = cls.get('grade_formula', {})
                tx1_weight = int(formula.get('regular_weight_1', 0.2) * 100)
                tx2_weight = int(formula.get('regular_weight_2', 0.3) * 100)
                ck_weight = int(formula.get('final_weight', 0.5) * 100)
                self.formula_label.configure(text=f"Công thức: TX1({tx1_weight}%) + TX2({tx2_weight}%) + CK({ck_weight}%)")
                # Load students and grades
                self.load_students_and_grades(cls.get('_id', cls.get('id')))
                break

    def load_students_and_grades(self, class_id):
        """Load danh sách sinh viên và điểm hiện tại"""
        # Get students in class
        students = api.get_course_class_students(class_id)
        # Get existing grades
        grades = api.get_course_class_grades(class_id)
        
        # Debug
        print(f"\n=== LOAD STUDENTS AND GRADES ===")
        print(f"Number of students: {len(students)}")
        print(f"Number of grades: {len(grades)}")
        if students:
            print(f"First student ID: {students[0].get('_id', students[0].get('id'))}")
        if grades:
            print(f"First grade student_id: {grades[0].get('student_id')}")
        
        # Merge data - keep student's _id, only merge grade scores
        grades_dict = {g['student_id']: g for g in grades}
        for student in students:
            student_id = student.get('_id', student.get('id'))
            if student_id in grades_dict:
                grade = grades_dict[student_id]
                # Only copy score fields, NOT student_id
                student['regular_score_1'] = grade.get('regular_score_1')
                student['regular_score_2'] = grade.get('regular_score_2')
                student['final_score'] = grade.get('final_score')
                student['total_score'] = grade.get('total_score')
        
        print(f"After merge, first student: {students[0] if students else 'none'}")
        print("=== END LOAD ===\n")
        
        self.display_grade_form(students)
    
    def display_grade_form(self, students):
        """Hiển thị form nhập điểm"""
        # Clear existing widgets
        for widget in self.table_content.winfo_children():
            widget.destroy()
        
        if not students:
            ctk.CTkLabel(self.table_content, text="Không có sinh viên nào trong lớp này",
                        font=self.FONT_NORMAL, text_color="#94A3B8").pack(pady=50)
            return
        
        self.students_data = students
        self.grade_entries = {}
        
        # Header
        header = ctk.CTkFrame(self.table_content, fg_color="#F1F5F9", corner_radius=8)
        header.pack(fill="x", pady=(0, 10))
        
        header_grid = ctk.CTkFrame(header, fg_color="transparent")
        header_grid.pack(fill="x", padx=15, pady=10)
        
        # Configure grid weights
        header_grid.grid_columnconfigure(0, weight=3)  # Name
        header_grid.grid_columnconfigure(1, weight=1)  # TX1
        header_grid.grid_columnconfigure(2, weight=1)  # TX2
        header_grid.grid_columnconfigure(3, weight=1)  # CK
        
        ctk.CTkLabel(header_grid, text="Họ và tên", font=("Ubuntu", 12, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkLabel(header_grid, text="TX1", font=("Ubuntu", 12, "bold")).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(header_grid, text="TX2", font=("Ubuntu", 12, "bold")).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header_grid, text="CK", font=("Ubuntu", 12, "bold")).grid(row=0, column=3, padx=5)
        
        # Student rows
        for i, student in enumerate(students):
            student_id = student.get('_id', student.get('id'))
            
            # Row frame
            row_frame = ctk.CTkFrame(self.table_content, fg_color="#FAFAFA" if i % 2 == 0 else "white", corner_radius=8)
            row_frame.pack(fill="x", pady=2)
            
            row_grid = ctk.CTkFrame(row_frame, fg_color="transparent")
            row_grid.pack(fill="x", padx=15, pady=8)
            
            # Configure grid weights
            row_grid.grid_columnconfigure(0, weight=3)
            row_grid.grid_columnconfigure(1, weight=1)
            row_grid.grid_columnconfigure(2, weight=1)
            row_grid.grid_columnconfigure(3, weight=1)
            
            # Student name
            name = student.get('full_name', 'Unknown')
            mssv = student.get('mssv', '')
            display_name = f"{name} ({mssv})" if mssv else name
            ctk.CTkLabel(row_grid, text=display_name, font=self.FONT_NORMAL, anchor="w").grid(row=0, column=0, padx=5, sticky="w")
            
            # Grade entries
            self.grade_entries[student_id] = {}
            
            # TX1
            tx1_var = ctk.StringVar(value=str(student.get('regular_score_1', '')) if student.get('regular_score_1') is not None else '')
            tx1_entry = ctk.CTkEntry(row_grid, textvariable=tx1_var, width=60, height=30, font=self.FONT_SMALL)
            tx1_entry.grid(row=0, column=1, padx=5)
            self.grade_entries[student_id]['tx1'] = tx1_var
            
            # TX2
            tx2_var = ctk.StringVar(value=str(student.get('regular_score_2', '')) if student.get('regular_score_2') is not None else '')
            tx2_entry = ctk.CTkEntry(row_grid, textvariable=tx2_var, width=60, height=30, font=self.FONT_SMALL)
            tx2_entry.grid(row=0, column=2, padx=5)
            self.grade_entries[student_id]['tx2'] = tx2_var
            
            # CK
            ck_var = ctk.StringVar(value=str(student.get('final_score', '')) if student.get('final_score') is not None else '')
            ck_entry = ctk.CTkEntry(row_grid, textvariable=ck_var, width=60, height=30, font=self.FONT_SMALL)
            ck_entry.grid(row=0, column=3, padx=5)
            self.grade_entries[student_id]['ck'] = ck_var
        
        # Enable save button
        self.save_btn.configure(state="normal")
    

    def save_grades(self):
        """Lưu điểm vào database"""
        if not self.selected_class or not self.grade_entries:
            return
        
        class_id = self.selected_class.get('_id', self.selected_class.get('id'))
        grades_data = []
        
        for student in self.students_data:
            student_id = student.get('_id', student.get('id'))
            if student_id not in self.grade_entries:
                continue
            
            entries = self.grade_entries[student_id]
            
            # Parse scores
            def parse_score(text):
                try:
                    score = float(text.strip()) if text.strip() else None
                    return score if score is not None and 0 <= score <= 10 else None
                except:
                    return None
            
            tx1 = parse_score(entries['tx1'].get())
            tx2 = parse_score(entries['tx2'].get())
            ck = parse_score(entries['ck'].get())
            
            grades_data.append({
                'student_id': student_id,
                'regular_score_1': tx1,
                'regular_score_2': tx2,
                'final_score': ck
            })
        
        # Debug: Print first 3 grades
        print("\n=== FRONTEND SAVE GRADES ===")
        print(f"Class ID: {class_id}")
        print(f"Total grades: {len(grades_data)}")
        for i, grade in enumerate(grades_data[:3]):
            print(f"Grade {i}: {grade}")
        
        # Save to backend
        success, result = api.save_course_grades(class_id, grades_data)
        
        print(f"Save result: success={success}, result={result}")
        print("=== END FRONTEND SAVE ===\n")
        
        if success:
            messagebox.showinfo("Thành công", "Đã lưu điểm thành công!")
            # Reload grades to show updated data
            self.load_students_and_grades(class_id)
        else:
            messagebox.showerror("Lỗi", f"Lưu điểm thất bại: {result}")


