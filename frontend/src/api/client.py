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
            res = self.session.post(f"{self.base_url}/auth/refresh")
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
    def get_dashboard_stats(self):
        # Mock data logic cho dashboard tổng quan
        role = self.user_info.get("role", "STUDENT")
        import time
        time.sleep(0.3) 
        if role == "STUDENT":
            return {"role": "STUDENT", "gpa_4": 3.2, "credits": 85, "tuition_status": True, "semester_grades": [2.5, 2.8, 3.0, 3.2]}
        # CVHT/ADMIN
        return {"role": role, "total_students": 60, "warning_count": 5, "debt_count": 10, "gpa_distribution": {"excellent": 5, "good": 20, "fair": 20, "average": 10, "weak": 5}}

    # --- CLASSES ---
    def get_my_classes(self):
        res = self.request("GET", "/classes/")
        return res.json() if res and res.status_code == 200 else []

    def create_class(self, name, semester):
        res = self.request("POST", "/classes/", json={"name": name, "semester": semester})
        return (True, "OK") if res and res.status_code == 200 else (False, "Error")
    
    def get_class_students(self, class_id):
        res = self.request("GET", f"/classes/{class_id}/students")
        return res.json() if res and res.status_code == 200 else []
    
    def remove_student(self, class_id, student_id):
        res = self.request("DELETE", f"/classes/{class_id}/students/{student_id}")
        return res.status_code == 200

    def import_students(self, class_id, file_path):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                # Dùng session trực tiếp để requests tự handle boundary multipart
                url = f"{self.base_url}/classes/{class_id}/import-students"
                # Header Authorization vẫn nằm trong session
                res = self.session.post(url, files=files)
                return (True, res.json()) if res.status_code == 200 else (False, res.json())
        except Exception as e: return (False, str(e))

    # --- GRADES ---
    def get_my_grades(self, semester=None):
        url = f"/grades/my-grades?semester={semester}" if semester else "/grades/my-grades"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []

    def get_class_grades(self, class_id, semester):
        res = self.request("GET", f"/grades/class/{class_id}?semester={semester}")
        return res.json() if res and res.status_code == 200 else []
    
    def import_grades(self, class_id, semester, file_path):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                url = f"{self.base_url}/grades/import"
                params = {'class_id': class_id, 'semester': semester}
                res = self.session.post(url, params=params, files=files)
                return (True, res.json()) if res.status_code == 200 else (False, res.json())
        except Exception as e: return (False, str(e))

    # --- CHAT ---
    def get_conversations(self):
        res = self.request("GET", "/conversations")
        return res.json() if res and res.status_code == 200 else []
    
    def get_messages(self, conv_id):
        res = self.request("GET", f"/conversations/{conv_id}/messages")
        return res.json() if res and res.status_code == 200 else []
    
    def create_conversation(self, receiver_id):
        res = self.request("POST", "/conversations", json={"receiver_id": receiver_id})
        return res.json() if res and res.status_code == 200 else None

    # --- FORUM ---
    def get_class_posts(self, class_id):
        res = self.request("GET", f"/classes/{class_id}/posts")
        return res.json() if res and res.status_code == 200 else []

    def create_post(self, class_id, content):
        res = self.request("POST", f"/classes/{class_id}/posts", json={"content": content})
        return (True, res.json()) if res and res.status_code == 200 else (False, None)

    def toggle_like(self, post_id):
        self.request("PUT", f"/posts/{post_id}/like")

    def add_comment(self, post_id, content):
        self.request("POST", f"/posts/{post_id}/comments", json={"content": content})

    # --- USERS (ADMIN) ---
    def get_all_users(self, role=None):
        url = f"/users/?role={role}" if role and role != "ALL" else "/users/"
        res = self.request("GET", url)
        return res.json() if res and res.status_code == 200 else []
    
    def update_user(self, user_id, data):
        res = self.request("PUT", f"/users/{user_id}", json=data)
        return (True, "OK") if res and res.status_code == 200 else (False, res.json().get('detail'))
    
    def delete_user(self, user_id):
        res = self.request("DELETE", f"/users/{user_id}")
        return (True, "OK") if res and res.status_code == 200 else (False, "Error")

    # --- STATS (CVHT) ---
    def get_class_stats(self, class_id, semester):
        res = self.request("GET", f"/stats/dashboard/{class_id}?semester={semester}")
        return res.json() if res and res.status_code == 200 else None

api = APIClient()