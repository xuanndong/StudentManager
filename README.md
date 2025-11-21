# Student Management System

Hệ thống quản lý sinh viên với phân quyền đầy đủ cho ADMIN, CVHT (Cố vấn học tập), TEACHER và STUDENT.

## Tính năng chính

### Phân quyền theo vai trò

**ADMIN**
- Quản lý tất cả người dùng trong hệ thống
- Tạo và quản lý danh mục môn học
- Xem toàn bộ dữ liệu hệ thống
- Quản lý lớp chính quy và lớp học phần

**CVHT (Cố vấn học tập)**
- Quản lý lớp chính quy của mình
- Import danh sách sinh viên từ Excel/CSV
- Xem thống kê học lực của lớp
- Tính toán GPA tự động từ điểm các môn
- Cập nhật thông tin nợ học phí, cảnh báo học vụ
- Quản lý forum lớp chính quy

**TEACHER (Giảng viên)**
- Tạo và quản lý lớp học phần
- Import danh sách sinh viên đăng ký môn học
- Nhập điểm cho sinh viên (giữa kỳ, cuối kỳ, bài tập)
- Quản lý forum lớp học phần
- Xem danh sách sinh viên trong lớp

**STUDENT (Sinh viên)**
- Xem điểm các môn học
- Xem tổng kết học kỳ và GPA
- Xem lớp chính quy và lớp học phần
- Tham gia forum thảo luận
- Chat với bạn cùng lớp, giảng viên, CVHT

### Quản lý lớp học

**Lớp chính quy (Administrative Class)**
- Quản lý bởi CVHT
- Nhóm sinh viên theo khóa học (ví dụ: CNTT-K17)
- Theo dõi học lực toàn khóa

**Lớp học phần (Course Class)**
- Quản lý bởi Teacher
- Dạy môn học cụ thể trong học kỳ
- Nhập điểm cho sinh viên đăng ký

### Quản lý điểm

**Điểm môn học (Course Grades)**
- Teacher nhập điểm từng môn
- Hỗ trợ nhiều thành phần: giữa kỳ, cuối kỳ, bài tập
- Công thức tính điểm linh hoạt theo từng môn
- Tự động tính điểm tổng kết

**Tổng kết học kỳ (Semester Summary)**
- Tự động tính GPA từ điểm các môn
- Tính số tín chỉ tích lũy
- Xếp loại học lực: Xuất sắc, Giỏi, Khá, Trung bình, Yếu
- Cảnh báo học vụ tự động

### Tính năng khác

- Forum thảo luận cho từng lớp
- Chat real-time với WebSocket
- Import dữ liệu từ Excel/CSV
- Dashboard thống kê trực quan
- Báo cáo phân bố điểm

## Cài đặt và chạy

### Yêu cầu hệ thống

- Python 3.8 trở lên
- MongoDB 4.0 trở lên
- Hệ điều hành: Windows, Linux, macOS

### Bước 1: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: Cấu hình

Tạo file `.env` từ `.env.example`:

```env
DATABASE_HOST=localhost
DATABASE_PORT=27017
DATABASE_NAME=qlsv_v2
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_EXPIRE=30
REFRESH_EXPIRE=7
API_V1_STR=/api/v1
```

### Bước 3: Khởi động MongoDB

```bash
# Linux/macOS
sudo systemctl start mongod

# Windows
net start MongoDB
```

### Bước 4: Import dữ liệu mẫu

```bash
python import_sample_data.py
```

Dữ liệu mẫu bao gồm:
- 1 ADMIN, 1 CVHT, 2 TEACHER, 3 STUDENT
- 5 môn học
- 1 lớp chính quy với 3 sinh viên
- 2 lớp học phần với điểm số
- Dữ liệu forum và chat

### Bước 5: Chạy ứng dụng

**Terminal 1 - Backend:**
```bash
python -m uvicorn app.main:app --reload --port 8080
```

**Terminal 2 - Frontend:**
```bash
python frontend/main.py
```

### Bước 6: Đăng nhập

Mở ứng dụng frontend và đăng nhập với các tài khoản sau:

**Password cho tất cả tài khoản: `password123`**

| Vai trò | MSSV | Tên | Mô tả |
|---------|------|-----|-------|
| ADMIN | ADMIN001 | Admin User | Quản trị viên hệ thống |
| CVHT | CVHT001 | Nguyen Van An | CVHT lớp CNTT-K17 |
| TEACHER | GV001 | Tran Thi Binh | Giảng viên Python |
| TEACHER | GV002 | Le Van Cuong | Giảng viên Database |
| STUDENT | 20201234 | Pham Thi Dung | Sinh viên xuất sắc (GPA 3.8) |
| STUDENT | 20201235 | Hoang Van Em | Sinh viên giỏi (GPA 3.2) |
| STUDENT | 20201236 | Nguyen Thi Phuong | Sinh viên khá (GPA 2.8) |

## Cấu trúc dự án

### Backend (FastAPI)

```
app/
├── main.py                      # Entry point, khởi tạo FastAPI
├── dependencies.py              # Authentication và phân quyền
├── core/
│   ├── security.py             # JWT, password hashing
│   └── socket.py               # WebSocket manager
├── db/
│   └── connection.py           # Kết nối MongoDB
├── model/                      # Pydantic models
│   ├── muser.py               # User model
│   ├── mcourse.py             # Course model
│   ├── madministrative_class.py
│   ├── mgrade.py              # Grade models
│   ├── mpost.py               # Forum post model
│   └── mchat.py               # Chat models
├── routers/                    # API endpoints
│   ├── auth.py                # Login, register
│   ├── users.py               # User management
│   ├── courses.py             # Course catalog
│   ├── administrative_classes.py
│   ├── classes.py             # Course classes
│   ├── course_grades.py       # Grade entry
│   ├── semester_summary.py    # GPA calculation
│   ├── posts.py               # Forum
│   ├── chat.py                # Chat & WebSocket
│   └── stats.py               # Statistics
└── utils/
    └── grade_calculator.py     # GPA calculation logic
```

### Frontend (CustomTkinter)

```
frontend/
├── main.py                     # Entry point
└── src/
    ├── api/
    │   └── client.py          # API client với authentication
    ├── components/
    │   └── sidebar.py         # Navigation sidebar
    └── views/                 # UI views
        ├── login_view.py
        ├── main_view.py
        ├── dashboard_view.py
        ├── users_view.py
        ├── courses_view.py
        ├── admin_classes_view.py
        ├── course_classes_view.py
        ├── course_grades_view.py
        ├── semester_summary_view.py
        ├── student_classes_view.py
        ├── student_grades_view.py
        ├── stats_view.py
        ├── forum_view.py
        └── chat_view.py
```

## Quy trình sử dụng

### Quy trình hoàn chỉnh từ đầu đến cuối

1. **ADMIN tạo môn học**
   - Vào menu "Courses"
   - Thêm môn học mới với mã môn, tên, số tín chỉ
   - Cấu hình công thức tính điểm (giữa kỳ, cuối kỳ, bài tập)

2. **CVHT tạo lớp chính quy**
   - Vào menu "Administrative Classes"
   - Tạo lớp mới (ví dụ: CNTT-K17)
   - Import danh sách sinh viên từ Excel/CSV

3. **TEACHER tạo lớp học phần**
   - Vào menu "My Courses"
   - Chọn môn học và tạo lớp học phần
   - Import danh sách sinh viên đăng ký

4. **TEACHER nhập điểm**
   - Vào menu "Grade Entry"
   - Chọn lớp học phần
   - Nhập điểm cho từng sinh viên

5. **CVHT tính GPA**
   - Vào menu "Semester Summary"
   - Hệ thống tự động tính GPA từ điểm các môn
   - Cập nhật thông tin nợ học phí, cảnh báo

6. **STUDENT xem điểm**
   - Vào menu "My Academic Records"
   - Xem điểm từng môn và GPA

## Database Schema

### Collections chính

**users**
- Lưu thông tin người dùng
- Fields: mssv, full_name, email, password, role, phone

**courses**
- Danh mục môn học
- Fields: course_code, course_name, credits, grade_formula

**administrative_classes**
- Lớp chính quy
- Fields: name, academic_year, advisor_id, student_ids

**course_classes**
- Lớp học phần
- Fields: course_id, teacher_id, semester, class_code, student_ids

**course_grades**
- Điểm từng môn
- Fields: student_id, course_class_id, midterm, final, assignment, total

**semester_summaries**
- Tổng kết học kỳ
- Fields: student_id, semester, gpa, credits_earned, academic_warning

**posts**
- Bài viết forum
- Fields: class_id, author_id, content, comments

**conversations & messages**
- Chat real-time
- Fields: participants, messages, timestamps

## API Documentation

Sau khi chạy backend, truy cập Swagger UI để xem tài liệu API đầy đủ:

```
http://localhost:8080/docs
```

API endpoints chính:

- POST /api/v1/auth/login - Đăng nhập
- GET /api/v1/users/ - Danh sách users
- GET /api/v1/courses/ - Danh sách môn học
- GET /api/v1/administrative-classes/ - Lớp chính quy
- GET /api/v1/course-classes/ - Lớp học phần
- POST /api/v1/course-grades/ - Nhập điểm
- GET /api/v1/semester-summary/ - Tổng kết học kỳ
- WebSocket /ws/{user_id} - Chat real-time

## Bảo mật

- Password được hash bằng bcrypt
- Authentication sử dụng JWT tokens
- Role-based access control (RBAC)
- HTTPOnly cookies cho refresh token
- Input validation với Pydantic
- Protected WebSocket connections


## Tính năng nổi bật

### Tính GPA tự động
- Không cần nhập thủ công
- Tự động tính từ điểm các môn học
- Cập nhật real-time khi có điểm mới

### Import dữ liệu linh hoạt
- Hỗ trợ Excel (.xlsx, .xls) và CSV
- Tự động mapping theo email hoặc MSSV
- Báo cáo chi tiết kết quả import

### Forum thảo luận
- Riêng biệt cho từng lớp
- Hiển thị tên và vai trò người đăng
- Hỗ trợ comments

### Chat real-time
- WebSocket cho tốc độ cao
- Chat với bạn cùng lớp
- Chat với giảng viên và CVHT
- Tìm kiếm người dùng theo số điện thoại

### Thống kê trực quan
- Biểu đồ phân bố điểm
- Thống kê theo lớp
- Dashboard tổng quan

## Phát triển tiếp

Các tính năng có thể bổ sung:

- Thông báo qua email
- Upload file đính kèm trong forum
- Ảnh đại diện người dùng
- Biểu đồ lịch sử điểm
- Quản lý điểm danh
- Quản lý thời khóa biểu
- Ứng dụng mobile
- Export báo cáo PDF/Excel
- Pagination cho danh sách lớn
- Rate limiting API
- Logging và monitoring

## License

MIT License - Tự do sử dụng cho mục đích học tập
