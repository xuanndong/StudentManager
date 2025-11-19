import requests
import os
from dotenv import load_dotenv

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:8080/api/v1')
        self.token = None
        self.user_info = None
        
        # Sử dụng Session để tự động quản lý Cookie (Refresh Token)
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def set_token(self, token):
        self.token = token
        # Cập nhật header cho các request tiếp theo
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def login(self, mssv, password):
        try:
            payload = {'mssv': mssv, 'password': password}
            # Dùng session.post thay vì requests.post
            response = self.session.post(f'{self.base_url}/auth/login', json=payload)

            if response.status_code == 200:
                data = response.json()
                self.set_token(data['access_token'])
                # Refresh token đã tự động nằm trong self.session.cookies
                return True, "Log in successfully"
            else:
                detail = response.json().get('detail', 'Unknown error')
                return False, detail
        except Exception as e:
            return False, f"Server connection error: {str(e)}"

    def refresh_access_token(self):
        """Gọi API refresh để lấy token mới bằng Cookie"""
        try:
            # Gửi request refresh (Cookie sẽ tự động được gửi kèm)
            response = self.session.post(f"{self.base_url}/auth/refresh")
            
            if response.status_code == 200:
                data = response.json()
                self.set_token(data['access_token'])
                return True
            return False
        except:
            return False

    def request(self, method, endpoint, **kwargs):
        """
        Hàm wrapper thông minh:
        Tự động gửi request -> Nếu lỗi 401 -> Tự Refresh Token -> Gửi lại
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Nếu gặp lỗi 401 (Unauthorized) -> Thử refresh token
            if response.status_code == 401:
                print("Token expired. Refreshing...")
                if self.refresh_access_token():
                    # Refresh thành công -> Gửi lại request cũ
                    print("Refresh success. Retrying request...")
                    response = self.session.request(method, url, **kwargs)
                else:
                    print("Refresh failed. Logout needed.")
                    # Refresh thất bại -> Coi như phiên đăng nhập hết hạn
                    
            return response
        except Exception as e:
            print(f"Request Error: {e}")
            return None

    def get_user_info(self):
        if not self.token: return None
        # Dùng hàm request thông minh ở trên
        res = self.request("GET", "/users/me")
        if res and res.status_code == 200:
            self.user_info = res.json()
            return self.user_info
        return None
        
    def logout(self):
        self.session.post(f"{self.base_url}/auth/logout")
        self.token = None
        self.user_info = None
        self.session.headers.pop("Authorization", None)
        self.session.cookies.clear()


    """
    ====== API STATISTICS ======
    """
    def get_dashboard_stats(self):
        """Lấy số liệu thống kê tùy theo Role của User"""
        role = self.user_info.get("role", "STUDENT")
        
        # Giả lập độ trễ mạng
        import time
        time.sleep(0.5)

        if role == "STUDENT":
            return {
                "role": "STUDENT",
                "gpa_4": 3.6,           # GPA hệ 4
                "gpa_10": 8.5,          # GPA hệ 10
                "credits": 85,          # Tín chỉ tích lũy
                "tuition_status": True, # True = Đã đóng, False = Nợ
                "semester_grades": [3.2, 3.4, 3.6, 3.5, 3.8] # Biểu đồ đường
            }
        else:
            # Dành cho CVHT / ADMIN
            return {
                "role": "CVHT",
                "total_students": 45,
                "warning_count": 3,
                "debt_count": 8,
                "gpa_distribution": {
                    "excellent": 5,
                    "good": 15,
                    "fair": 12,
                    "average": 10,
                    "weak": 3
                }
            }
    
    """
    ====== API CLASS ======
    """
    def get_my_classes(self):
        """Lấy danh sách lớp học"""
        if not self.token: return []
        res = self.request("GET", "/classes/")
        if res and res.status_code == 200:
            return res.json()
        return [] # Trả về list rỗng nếu lỗi


    def create_class(self, name, semester):
        """Tạo lớp mới (Chỉ CVHT)"""
        payload = {"name": name, "semester": semester}
        res = self.request("POST", "/classes/", json=payload)
        if res and res.status_code == 200:
            return True, "Class created successfully"
        elif res:
            return False, res.json().get("detail", "Error creating class")
        return False, "Connection error"
    
    """
    ====== API GRADE ======
    """
    def get_my_grades(self, semester=None):
        """Sinh viên xem điểm"""
        endpoint = "/grades/my-grades"
        if semester:
            endpoint += f"?semester={semester}"
        
        res = self.request("GET", endpoint)
        return res.json() if res and res.status_code == 200 else []


    def get_class_grades(self, class_id, semester):
        """CVHT xem điểm lớp"""
        endpoint = f"/grades/class/{class_id}?semester={semester}"
        res = self.request("GET", endpoint)
        return res.json() if res and res.status_code == 200 else []


    def import_grades(self, class_id, semester, file_path):
        """Upload file Excel"""
        try:
            # Mở file dưới dạng binary
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                # Params gửi kèm trên URL
                params = {'class_id': class_id, 'semester': semester}
                
                # Gửi request (Lưu ý: không dùng json=, mà dùng files=)
                # Ta phải gọi trực tiếp session để handle multipart/form-data
                url = f"{self.base_url}/grades/import"
                response = self.session.post(url, params=params, files=files)
                
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, response.json().get("detail", "Upload failed")
        except Exception as e:
            return False, str(e)
    
    """
    ====== API CHAT REAL TIME ======
    """
    def get_conversations(self):
        """Lấy danh sách các cuộc hội thoại"""
        res = self.request("GET", "/conversations")
        return res.json() if res and res.status_code == 200 else []

    def get_messages(self, conversation_id):
        """Lấy lịch sử tin nhắn của 1 hội thoại"""
        res = self.request("GET", f"/conversations/{conversation_id}/messages")
        return res.json() if res and res.status_code == 200 else []

    def create_conversation(self, receiver_id):
        """Bắt đầu chat với người mới"""
        res = self.request("POST", "/conversations", json={"receiver_id": receiver_id})
        return res.json() if res and res.status_code == 200 else None

    
    """
    ====== API FORUM ======
    """
    def get_class_posts(self, class_id):
        """Lấy danh sách bài viết của một lớp"""
        res = self.request("GET", f"/classes/{class_id}/posts")
        return res.json() if res and res.status_code == 200 else []

    def create_post(self, class_id, content):
        """Đăng bài viết mới"""
        res = self.request("POST", f"/classes/{class_id}/posts", json={"content": content})
        return res.json() if res and res.status_code == 200 else None

    def toggle_like(self, post_id):
        """Thả tim / Bỏ tim"""
        res = self.request("PUT", f"/posts/{post_id}/like")
        return res.json() if res and res.status_code == 200 else None

    def add_comment(self, post_id, content):
        """Bình luận"""
        res = self.request("POST", f"/posts/{post_id}/comments", json={"content": content})
        return res.json() if res and res.status_code == 200 else None


api = APIClient()