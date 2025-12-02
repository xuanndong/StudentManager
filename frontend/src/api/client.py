import requests
import os
from dotenv import load_dotenv

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8080/api/v1')
        self.token = None
        self.user_info = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def set_token(self, token):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401:
                if self.refresh_access_token():
                    return self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def refresh_access_token(self):
        try:
            res = self.session.post(f"{self.base_url.replace('/api/v1', '')}/api/v1/auth/refresh")
            if res.status_code == 200:
                self.set_token(res.json()['access_token'])
                return True
        except: pass
        return False

    # --- AUTH ---
    def login(self, mssv, password):
        try:
            res = self.session.post(f'{self.base_url}/auth/login', json={'mssv': mssv, 'password': password})
            if res.status_code == 200:
                self.set_token(res.json()['access_token'])
                return True, "Success"
            return False, res.json().get('detail', 'Login failed')
        except Exception as e: return False, str(e)

    def get_user_info(self):
        res = self.request("GET", "/users/me")
        if res and res.status_code == 200:
            self.user_info = res.json()
            return self.user_info
        return None

    def logout(self):
        self.session.post(f"{self.base_url}/auth/logout")
        self.token = None
        self.user_info = None

    # --- DASHBOARD ---
    def get_dashboard_stats(self, class_id=None, semester=None):
        """Lấy thống kê dashboard - tính real-time từ course_grades"""
        role = self.user_info.get("role", "STUDENT") if self.user_info else "STUDENT"

        if role == "STUDENT":
            # Gọi API tính toán real-time
            res = self.request("GET", "/course-grades/my-stats")
            if res and res.status_code == 200:
                stats = res.json()
                return {
                    "role": "STUDENT",
                    "gpa_4": stats.get("overall_gpa", 0.0),
                    "credits": stats.get("total_credits", 0),
                    "tuition_status": True,  # Có thể lấy từ semester_summaries nếu cần
                    "semester_grades": stats.get("semester_gpas", [])
                }
            return {"role": "STUDENT", "gpa_4": 0.0, "credits": 0, "tuition_status": True, "semester_grades": []}
        
        elif role == "CVHT":
            # CVHT xem thống kê lớp
            if not class_id or not semester:
                return None
            res = self.request("GET", f"/stats/dashboard/{class_id}?semester={semester}")
            if res and res.status_code == 200:
                data = res.json()
                data['role'] = role
                return data
            return None
        
        return None

    # --- BACKWARD COMPATIBILITY ---
    def get_my_classes(self, semester=None):
        """DEPRECATED: Tương thích ngược với code cũ"""
        role = self.user_info.get("role", "STUDENT") if self.user_info else "STUDENT"
        
        if role == "CVHT":
            return self.get_my_administrative_classes()
        elif role == "TEACHER":
            return self.get_my_course_classes(semester)
        elif role == "STUDENT":
            # Student có thể xem cả 2 loại lớp
            admin = self.get_my_administrative_classes()
            courses = self.get_my_course_classes(semester)
            return admin + courses
        return []
    
    def get_class_posts(self, class_id):
        """DEPRECATED: Tương thích ngược"""
        # Try administrative first, then course
        posts = self.get_administrative_posts(class_id)
        if not posts:
            posts = self.get_course_posts(class_id)
        return posts
    
    def create_post(self, class_id, content):
        """DEPRECATED: Tương thích ngược"""
        # Try administrative first
        success, result = self.create_administrative_post(class_id, content)
        if not success:
            success, result = self.create_course_post(class_id, content)
        return (success, result)
    
    def get_class_students(self, class_id):
        """DEPRECATED: Tương thích ngược"""
        students = self.get_administrative_class_students(class_id)
        if not students:
            students = self.get_course_class_students(class_id)
        return students
    
    def import_students(self, class_id, file_path):
        """DEPRECATED: Chỉ import vào lớp chính quy"""
        return self.import_administrative_students(class_id, file_path)
    
    def remove_student(self, class_id, student_id):
        """DEPRECATED: Tương thích ngược"""
        success = self.remove_administrative_student(class_id, student_id)
        return success
    
    def create_class(self, name, semester):
        """DEPRECATED: Tương thích ngược - tạo administrative class"""
        return self.create_administrative_class(name, semester)
    
    def get_my_grades(self, semester=None):
        """DEPRECATED: Tương thích ngược"""
        return self.get_my_semester_summary(semester)
    
    def get_class_grades(self, class_id, semester):
        """DEPRECATED: Tương thích ngược"""
        return self.get_class_semester_summary(class_id, semester)
    
    def import_grades(self, class_id, semester, file_path):
        """DEPRECATED: Tương thích ngược"""
        # This is complex, just return error for now
        return (False, "Please use new Semester Summary feature")
    
    def get_class_stats(self, class_id, semester):
        """Get stats for dashboard"""
        res = self.request("GET", f"/stats/dashboard/{class_id}?semester={semester}")
        if res and res.status_code == 200:
            data = res.json()
            # Convert gpa_distribution to Vietnamese labels
            if 'gpa_distribution' in data:
                dist = data['gpa_distribution']
                data['gpa_distribution'] = {
                    'Xuất sắc': dist.get('excellent', 0),
                    'Giỏi': dist.get('good', 0),
                    'Khá': dist.get('fair', 0),
                    'Trung bình': dist.get('average', 0),
                    'Yếu': dist.get('weak', 0)
                }
            return data
        return None

    # --- ADMINISTRATIVE CLASSES (CVHT) ---
    def get_my_administrative_classes(self):
        """Lấy danh sách lớp chính quy"""
        res = self.request("GET", "/administrative-classes/")
        return res.json() if res and res.status_code == 200 else []

    def create_administrative_class(self, name, academic_year):
        """Tạo lớp chính quy"""
        res = self.request("POST", "/administrative-classes/", json={"name": name, "academic_year": academic_year})
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")

    def get_administrative_class_students(self, class_id):
        """Lấy danh sách sinh viên lớp chính quy"""
        res = self.request("GET", f"/administrative-classes/{class_id}/students")
        return res.json() if res and res.status_code == 200 else []

    def remove_administrative_student(self, class_id, student_id):
        """Xóa sinh viên khỏi lớp chính quy"""
        res = self.request("DELETE", f"/administrative-classes/{class_id}/students/{student_id}")
        return res.status_code == 200

    # --- COURSES (ADMIN/TEACHER) ---
    def get_all_courses(self):
        """Lấy danh sách môn học"""
        res = self.request("GET", "/courses")
        return res.json() if res and res.status_code == 200 else []

    def create_course(self, code, name, credits):
        """Tạo môn học (ADMIN)"""
        res = self.request("POST", "/courses", json={"code": code, "name": name, "credits": credits})
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")
    
    def update_course(self, course_id, name, credits):
        """Cập nhật môn học (ADMIN)"""
        res = self.request("PUT", f"/courses/{course_id}", json={"name": name, "credits": credits})
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")
    
    def delete_course(self, course_id):
        """Xóa môn học (ADMIN)"""
        res = self.request("DELETE", f"/courses/{course_id}")
        return (True, None) if res and res.status_code == 200 else (False, "Error")

    # --- COURSE CLASSES (TEACHER) ---
    def get_my_course_classes(self, semester=None):
        """Lấy danh sách lớp học phần"""
        url = f"/course-classes?semester={semester}" if semester else "/course-classes"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []

    def create_course_class(self, course_id, semester, class_code):
        """Tạo lớp học phần (TEACHER)"""
        res = self.request("POST", "/course-classes", json={
            "course_id": course_id,
            "semester": semester,
            "class_code": class_code
        })
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")

    def get_course_class_students(self, class_id):
        """Lấy danh sách sinh viên lớp học phần"""
        res = self.request("GET", f"/course-classes/{class_id}/students")
        return res.json() if res and res.status_code == 200 else []



    # --- COURSE GRADES (TEACHER) ---
    
    def save_course_grades(self, course_class_id, grades_data):
        """Lưu điểm cho lớp học phần"""
        try:
            url = f"{self.base_url}/course-grades/save"
            data = {
                'course_class_id': course_class_id,
                'grades': grades_data
            }
            res = self.session.post(url, json=data, headers={"Authorization": f"Bearer {self.token}"})
            return (True, res.json()) if res.status_code == 200 else (False, res.json())
        except Exception as e: 
            return (False, str(e))

    def get_my_course_grades(self, semester=None):
        """Sinh viên xem điểm các môn"""
        url = f"/course-grades/my-grades?semester={semester}" if semester else "/course-grades/my-grades"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []

    def get_course_class_grades(self, class_id):
        """Giáo viên xem bảng điểm lớp học phần"""
        res = self.request("GET", f"/course-grades/course-class/{class_id}")
        return res.json() if res and res.status_code == 200 else []

    # --- SEMESTER SUMMARY (CVHT) ---
    def calculate_semester_summary(self, class_id, semester):
        """Tính toán tổng kết học kỳ cho cả lớp"""
        res = self.request("POST", f"/semester-summary/calculate-class/{class_id}?semester={semester}")
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")

    def get_my_semester_summary(self, semester=None):
        """Sinh viên xem tổng kết học kỳ"""
        url = f"/semester-summary/my-summary?semester={semester}" if semester else "/semester-summary/my-summary"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []

    def get_class_semester_summary(self, class_id, semester):
        """CVHT xem tổng kết học kỳ của lớp"""
        res = self.request("GET", f"/semester-summary/class/{class_id}?semester={semester}")
        return res.json() if res and res.status_code == 200 else []

    def update_semester_summary(self, summary_id, data):
        """CVHT cập nhật nợ học phí, cảnh báo"""
        res = self.request("PUT", f"/semester-summary/{summary_id}", json=data)
        return (True, res.json()) if res and res.status_code == 200 else (False, "Error")

    # --- POSTS/FORUM ---
    def get_administrative_posts(self, class_id, skip=0, limit=50):
        """Lấy bài đăng lớp chính quy"""
        res = self.request("GET", f"/posts/administrative-classes/{class_id}/posts?skip={skip}&limit={limit}")
        return res.json() if res and res.status_code == 200 else []

    def create_administrative_post(self, class_id, content):
        """Tạo bài đăng lớp chính quy"""
        res = self.request("POST", f"/posts/administrative-classes/{class_id}/posts", json={"content": content})
        return (True, res.json()) if res and res.status_code == 200 else (False, None)

    def get_course_posts(self, class_id, skip=0, limit=50):
        """Lấy bài đăng lớp học phần"""
        res = self.request("GET", f"/posts/course-classes/{class_id}/posts?skip={skip}&limit={limit}")
        return res.json() if res and res.status_code == 200 else []

    def create_course_post(self, class_id, content):
        """Tạo bài đăng lớp học phần"""
        res = self.request("POST", f"/posts/course-classes/{class_id}/posts", json={"content": content})
        return (True, res.json()) if res and res.status_code == 200 else (False, None)
    
    def get_user_by_id(self, user_id):
        """Lấy thông tin user theo ID"""
        res = self.request("GET", f"/users/{user_id}")
        return res.json() if res and res.status_code == 200 else None

    def toggle_like(self, post_id):
        """Like/Unlike bài viết"""
        self.request("PUT", f"/posts/{post_id}/like")

    def add_comment(self, post_id, content):
        """Thêm comment"""
        self.request("POST", f"/posts/{post_id}/comments", json={"content": content})

    def delete_post(self, post_id):
        """Xóa bài viết"""
        res = self.request("DELETE", f"/posts/{post_id}")
        return res.status_code == 200

    def update_post(self, post_id, content):
        """Sửa bài viết"""
        res = self.request("PUT", f"/posts/{post_id}", json={"content": content})
        return res.status_code == 200

    # --- CHAT ---
    def get_conversations(self):
        """Lấy danh sách hội thoại"""
        res = self.request("GET", "/conversations")
        return res.json() if res and res.status_code == 200 else []

    def get_messages(self, conv_id):
        """Lấy tin nhắn trong hội thoại"""
        res = self.request("GET", f"/conversations/{conv_id}/messages")
        return res.json() if res and res.status_code == 200 else []

    def create_conversation(self, receiver_id):
        """Tạo hội thoại mới theo ID"""
        res = self.request("POST", "/conversations", json={"receiver_id": receiver_id})
        return res.json() if res and res.status_code == 200 else None
    
    def search_user_by_phone(self, phone):
        """Tìm user theo số điện thoại"""
        res = self.request("GET", f"/users/search-by-phone/{phone}")
        return res.json() if res and res.status_code == 200 else None
    
    def create_conversation_by_phone(self, phone):
        """Tạo hội thoại mới theo số điện thoại"""
        res = self.request("POST", f"/conversations/by-phone?phone={phone}")
        return res.json() if res and res.status_code == 200 else None

    # --- USERS (ADMIN) ---
    def get_all_users(self, role=None):
        """Lấy danh sách users"""
        url = f"/users/?role={role}" if role and role != "ALL" else "/users/"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []

    def update_user(self, user_id, data):
        """Cập nhật thông tin user"""
        res = self.request("PUT", f"/users/{user_id}", json=data)
        return (True, "OK") if res and res.status_code == 200 else (False, res.json().get('detail') if res else "Error")

    def delete_user(self, user_id):
        """Xóa user"""
        res = self.request("DELETE", f"/users/{user_id}")
        return (True, "OK") if res and res.status_code == 200 else (False, "Error")
    
    # --- AI ASSISTANT ---
    def chat_with_ai(self, message, context=None):
        """Chat with AI assistant"""
        res = self.request("POST", "/ai/chat", json={"message": message, "context": context})
        if res and res.status_code == 200:
            data = res.json()
            return data.get('response')
        return None
    
    def check_ai_health(self):
        """Check if AI service is available"""
        res = self.request("GET", "/ai/health")
        return res.json() if res and res.status_code == 200 else {"available": False}

api = APIClient()
