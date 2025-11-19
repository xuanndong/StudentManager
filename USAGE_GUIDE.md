# Hướng dẫn sử dụng Student Management System

## Đăng nhập

1. Mở ứng dụng frontend
2. Nhập MSSV và mật khẩu
3. Hệ thống sẽ tự động chuyển đến dashboard phù hợp với role

## Chức năng theo Role

### STUDENT (Sinh viên)

#### Dashboard
- Xem GPA hiện tại (thang điểm 4.0)
- Xem tổng số tín chỉ đã tích lũy
- Kiểm tra trạng thái học phí
- Biểu đồ xu hướng điểm qua các kỳ

#### My Classes (Lớp học của tôi)
- Xem danh sách các lớp đã tham gia
- Xem thông tin chi tiết lớp
- Xem danh sách bạn cùng lớp

#### My Grades (Điểm của tôi)
- Xem bảng điểm theo từng kỳ
- Lọc điểm theo học kỳ
- Xem chi tiết: GPA, tín chỉ, cảnh báo học vụ, nợ học phí

#### Class Forum (Diễn đàn lớp)
- Chọn lớp để xem bài viết
- Đăng bài viết mới
- Like/Unlike bài viết
- Comment vào bài viết
- Xem và tương tác với bài viết của bạn cùng lớp

#### Messages (Tin nhắn)
- Chat realtime với bạn bè và giáo viên
- Xem lịch sử tin nhắn
- Tạo cuộc hội thoại mới

---

### CVHT (Cố vấn học tập)

#### Dashboard
- Xem tổng số sinh viên
- Số lượng sinh viên bị cảnh báo học vụ
- Số lượng sinh viên nợ học phí
- Biểu đồ phân bố điểm của lớp

#### Manage Classes (Quản lý lớp)
- Tạo lớp học mới
- Xem danh sách lớp đang quản lý
- Xem chi tiết từng lớp
- **Import sinh viên từ Excel/CSV**:
  - Chuẩn bị file Excel có cột `mssv` hoặc `email`
  - Click "Import Students"
  - Chọn file và upload
  - Hệ thống sẽ tự động thêm sinh viên vào lớp
- Xóa sinh viên khỏi lớp

#### Manage Grades (Quản lý điểm)
- Chọn lớp và học kỳ
- Xem bảng điểm của cả lớp
- **Import điểm từ Excel/CSV**:
  - Chuẩn bị file Excel với các cột:
    - `mssv` (bắt buộc)
    - `gpa` hoặc `điểm` (bắt buộc)
    - `credits` hoặc `tín chỉ`
    - `warning` hoặc `cảnh báo`
    - `debt` hoặc `nợ học phí`
  - Click "Import Excel"
  - Chọn file và upload
  - Xem kết quả import

#### Statistics (Thống kê)
- Chọn lớp và học kỳ
- Xem thống kê tổng quan:
  - Tổng số sinh viên
  - Số sinh viên cảnh báo
  - Số sinh viên nợ học phí
- Biểu đồ phân bố điểm:
  - Pie chart: Tỷ lệ phần trăm
  - Bar chart: Số lượng sinh viên theo từng mức điểm

#### Forum (Diễn đàn)
- Quản lý bài viết trong các lớp
- Đăng thông báo cho sinh viên
- Xóa bài viết không phù hợp
- Tương tác với sinh viên

#### Messages (Tin nhắn)
- Chat với sinh viên
- Tư vấn học tập
- Thông báo cá nhân

---

### ADMIN (Quản trị viên)

#### Dashboard
- Xem tổng quan toàn hệ thống
- Thống kê tổng hợp

#### User Management (Quản lý người dùng)
- Xem danh sách tất cả người dùng
- Lọc theo role (STUDENT, CVHT, ADMIN)
- **Chỉnh sửa thông tin người dùng**:
  - Click "Edit" trên dòng người dùng
  - Cập nhật: Họ tên, Email, Role, Trạng thái
  - Lưu thay đổi
- **Xóa người dùng**:
  - Click "Delete"
  - Xác nhận xóa
- Kích hoạt/Vô hiệu hóa tài khoản

#### All Classes (Tất cả lớp học)
- Xem tất cả lớp trong hệ thống
- Truy cập chi tiết bất kỳ lớp nào

#### All Grades (Tất cả điểm)
- Xem điểm của tất cả sinh viên
- Lọc theo lớp và học kỳ

#### Forum & Messages
- Toàn quyền quản lý
- Xóa nội dung vi phạm

---

## Tips & Tricks

### Import dữ liệu
1. **Chuẩn bị file Excel/CSV đúng format**
   - Đảm bảo có đủ các cột bắt buộc
   - Dữ liệu sạch, không có ô trống ở cột quan trọng

2. **Kiểm tra kết quả import**
   - Sau khi import, hệ thống sẽ hiển thị số lượng thành công
   - Nếu có lỗi, xem danh sách lỗi để sửa

### Sử dụng Forum hiệu quả
- Đặt tiêu đề rõ ràng cho bài viết
- Sử dụng comment thay vì tạo bài viết mới cho câu hỏi nhỏ
- CVHT nên pin các thông báo quan trọng

### Chat
- Tin nhắn được gửi realtime
- Nhấn Enter để gửi nhanh
- Lịch sử tin nhắn được lưu trữ

### Bảo mật
- Đăng xuất sau khi sử dụng xong
- Không chia sẻ mật khẩu
- CVHT và ADMIN cần bảo vệ thông tin sinh viên

---

## Xử lý sự cố

### Không kết nối được server
- Kiểm tra backend đã chạy chưa
- Kiểm tra URL trong file `.env`
- Kiểm tra firewall

### Import file bị lỗi
- Kiểm tra format file (Excel .xlsx hoặc CSV)
- Đảm bảo tên cột đúng
- Kiểm tra dữ liệu không có ký tự đặc biệt

### Chat không hoạt động
- Kiểm tra WebSocket server đang chạy
- Refresh lại ứng dụng
- Kiểm tra kết nối mạng

### Không thấy dữ liệu
- Đảm bảo đã chọn đúng lớp/học kỳ
- Click nút Refresh (↻)
- Kiểm tra quyền truy cập

---

## Liên hệ hỗ trợ

Nếu gặp vấn đề, vui lòng liên hệ:
- Email: support@sms.edu.vn
- Hotline: 1900-xxxx
