import customtkinter as ctk
from src.api.client import api

class StudentGradesView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.FONT_TITLE = ("Ubuntu", 18, "bold")
        self.FONT_NORMAL = ("Ubuntu", 13)
        self.FONT_SMALL = ("Ubuntu", 11)
        
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Header
        ctk.CTkLabel(self, text="My Academic Records", font=self.FONT_TITLE,
                    text_color="#1E293B").pack(anchor="w", pady=(0, 20))
        
        # Semester Summary
        summary_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        summary_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(summary_frame, text="Semester Summary", font=("Ubuntu", 16, "bold"),
                    text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        self.summary_content = ctk.CTkScrollableFrame(summary_frame, fg_color="transparent", height=200)
        self.summary_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Course Grades
        grades_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        grades_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(grades_frame, text="Course Grades", font=("Ubuntu", 16, "bold"),
                    text_color="#334155").pack(padx=20, pady=(20, 10), anchor="w")
        
        self.grades_content = ctk.CTkScrollableFrame(grades_frame, fg_color="transparent")
        self.grades_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_data(self):
        """Load điểm"""
        # Load semester summaries
        summaries = api.get_my_semester_summary()
        
        for w in self.summary_content.winfo_children():
            w.destroy()
        
        if not summaries:
            ctk.CTkLabel(self.summary_content, text="No semester summary available",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
        else:
            # Header
            header = ctk.CTkFrame(self.summary_content, fg_color="#F1F5F9", corner_radius=0)
            header.pack(fill="x", pady=(0, 5))
            
            cols = ["Semester", "GPA", "Credits", "Passed", "Debt", "Warning"]
            for col in cols:
                ctk.CTkLabel(header, text=col, font=("Ubuntu", 11, "bold"),
                            text_color="#475569").pack(side="left", expand=True, fill="x", padx=8, pady=8)
            
            # Rows
            for summary in summaries:
                row = ctk.CTkFrame(self.summary_content, fg_color="#F8FAFC", corner_radius=0)
                row.pack(fill="x", pady=2)
                
                gpa = summary.get('gpa', 0)
                gpa_color = "#10B981" if gpa >= 3.2 else "#F59E0B" if gpa >= 2.5 else "#EF4444"
                
                ctk.CTkLabel(row, text=summary.get('semester', 'N/A'), font=self.FONT_SMALL,
                            text_color="#334155").pack(side="left", expand=True, fill="x", padx=8, pady=8)
                ctk.CTkLabel(row, text=f"{gpa:.2f}", font=("Ubuntu", 11, "bold"),
                            text_color=gpa_color).pack(side="left", expand=True, fill="x", padx=8, pady=8)
                ctk.CTkLabel(row, text=str(summary.get('credits_earned', 0)), font=self.FONT_SMALL,
                            text_color="#334155").pack(side="left", expand=True, fill="x", padx=8, pady=8)
                ctk.CTkLabel(row, text=str(summary.get('credits_passed', 0)), font=self.FONT_SMALL,
                            text_color="#334155").pack(side="left", expand=True, fill="x", padx=8, pady=8)
                
                debt_text = "Yes" if summary.get('tuition_debt') else "No"
                debt_color = "#EF4444" if summary.get('tuition_debt') else "#10B981"
                ctk.CTkLabel(row, text=debt_text, font=self.FONT_SMALL,
                            text_color=debt_color).pack(side="left", expand=True, fill="x", padx=8, pady=8)
                
                warning = summary.get('academic_warning', 0)
                warning_color = "#EF4444" if warning > 0 else "#64748B"
                ctk.CTkLabel(row, text=str(warning), font=self.FONT_SMALL,
                            text_color=warning_color).pack(side="left", expand=True, fill="x", padx=8, pady=8)
        
        # Load course grades
        grades = api.get_my_course_grades()
        
        for w in self.grades_content.winfo_children():
            w.destroy()
        
        if not grades:
            ctk.CTkLabel(self.grades_content, text="No course grades available",
                        font=self.FONT_SMALL, text_color="#94A3B8").pack(pady=20)
        else:
            # Header
            header = ctk.CTkFrame(self.grades_content, fg_color="#F1F5F9", corner_radius=0)
            header.pack(fill="x", pady=(0, 5))
            
            cols = ["Course Class", "Midterm", "Final", "Assignment", "Total"]
            for col in cols:
                ctk.CTkLabel(header, text=col, font=("Ubuntu", 11, "bold"),
                            text_color="#475569").pack(side="left", expand=True, fill="x", padx=10, pady=8)
            
            # Rows
            for grade in grades:
                row = ctk.CTkFrame(self.grades_content, fg_color="#F8FAFC", corner_radius=0)
                row.pack(fill="x", pady=2)
                
                # Display course name instead of ID
                course_name = grade.get('course_name', grade.get('class_code', 'Unknown'))
                semester = grade.get('semester', '')
                display_text = f"{course_name} ({semester})" if semester else course_name
                
                ctk.CTkLabel(row, text=display_text,
                            font=self.FONT_SMALL, text_color="#334155").pack(side="left", expand=True,
                                                                             fill="x", padx=10, pady=8)
                
                for key in ['midterm_score', 'final_score', 'assignment_score', 'total_score']:
                    val = grade.get(key)
                    text = f"{val:.1f}" if val is not None else "—"
                    color = "#10B981" if val and val >= 8.0 else "#F59E0B" if val and val >= 5.0 else "#EF4444" if val else "#94A3B8"
                    ctk.CTkLabel(row, text=text, font=self.FONT_SMALL,
                                text_color=color).pack(side="left", expand=True, fill="x", padx=10, pady=8)
