from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Lưu danh sách kết nối đang hoạt động: {user_id: WebSocket}
        self.active_connections: str | WebSocket = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: str):
        """Gửi tin nhắn cho 1 user cụ thể nếu họ đang online"""
        if user_id in self.active_connections:
            connection = self.active_connections[user_id]
            # Gửi dưới dạng JSON
            await connection.send_json(message)


# Tạo instance global
manager = ConnectionManager()