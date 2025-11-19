# Student Management System (SMS)

Hệ thống quản lý sinh viên với giao diện desktop (CustomTkinter) và backend API (FastAPI + MongoDB).

## Tính năng chính

### Phân quyền 3 cấp:
- **STUDENT**: Xem điểm, lớp học, tham gia forum, chat
- **CVHT (Cố vấn học tập)**: Quản lý lớp, nhập điểm, thống kê, forum
- **ADMIN**: Quản lý người dùng, toàn quyền hệ thống

### Chức năng:
- 📊 Dashboard với thống kê theo role
- 👥 Quản lý lớp học và sinh viên
- 📝 Quản lý điểm (import Excel/CSV)
- 💬 Forum lớp học (đăng bài, like, comment)
- 💬 Chat realtime (WebSocket)
- 📈 Thống kê và biểu đồ

## Cài đặt

### Backend
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình .env
cp .env.example .env
# Chỉnh sửa .env với thông tin MongoDB

# Chạy server
cd app
uvicorn main:app --reload --port 8080
```

### Frontend
```bash
# Cài đặt dependencies (đã có trong requirements.txt)
pip install customtkinter pillow matplotlib websocket-client

# Chạy ứng dụng
cd frontend
python main.py
```

## Cấu trúc dự án

```
├── app/                    # Backend API
│   ├── routers/           # API endpoints
│   ├── model/             # Pydantic models
│   ├── core/              # Security, socket
│   └── db/                # Database connection
├── frontend/              # Desktop GUI
│   ├── src/
│   │   ├── views/        # Các màn hình
│   │   ├── components/   # Components tái sử dụng
│   │   └── api/          # API client
│   └── assets/           # Icons, images
└── requirements.txt
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Đăng nhập
- `POST /api/v1/auth/logout` - Đăng xuất
- `POST /api/v1/auth/refresh` - Refresh token

### Users (ADMIN only)
- `GET /api/v1/users/` - Danh sách người dùng
- `GET /api/v1/users/me` - Thông tin user hiện tại
- `PUT /api/v1/users/{mssv}` - Cập nhật user
- `DELETE /api/v1/users/{mssv}` - Xóa user

### Classes
- `GET /api/v1/classes/` - Danh sách lớp của tôi
- `POST /api/v1/classes/` - Tạo lớp (CVHT)
- `GET /api/v1/classes/{id}/students` - Danh sách sinh viên
- `POST /api/v1/classes/{id}/import-students` - Import sinh viên (CVHT)
- `DELETE /api/v1/classes/{id}/students/{mssv}` - Xóa sinh viên (CVHT)

### Grades
- `GET /api/v1/grades/my-grades` - Điểm của tôi (STUDENT)
- `GET /api/v1/grades/class/{id}` - Điểm lớp (CVHT)
- `POST /api/v1/grades/import` - Import điểm (CVHT)

### Forum
- `GET /api/v1/classes/{id}/posts` - Danh sách bài viết
- `POST /api/v1/classes/{id}/posts` - Tạo bài viết
- `PUT /api/v1/posts/{id}/like` - Like/Unlike
- `POST /api/v1/posts/{id}/comments` - Comment
- `DELETE /api/v1/posts/{id}` - Xóa bài viết

### Chat
- `GET /api/v1/conversations` - Danh sách hội thoại
- `POST /api/v1/conversations` - Tạo hội thoại
- `GET /api/v1/conversations/{id}/messages` - Lịch sử tin nhắn
- `WS /api/v1/ws/{user_id}` - WebSocket realtime

### Statistics (CVHT)
- `GET /api/v1/stats/dashboard/{class_id}` - Thống kê lớp

## Format file Import

### Import sinh viên (Excel/CSV)
Cần có cột: `mssv` hoặc `email`

### Import điểm (Excel/CSV)
Các cột bắt buộc:
- `mssv` - Mã sinh viên
- `gpa` hoặc `điểm` - Điểm trung bình
- `credits` hoặc `tín chỉ` - Số tín chỉ (optional)
- `warning` hoặc `cảnh báo` - Mức cảnh báo (optional)
- `debt` hoặc `nợ học phí` - Nợ học phí (optional)

## Ghi chú

- API register không được triển khai ở frontend (theo yêu cầu)
- WebSocket chat yêu cầu backend đang chạy
- Dashboard hiển thị dữ liệu mock nếu chưa có API thực

## License

MIT