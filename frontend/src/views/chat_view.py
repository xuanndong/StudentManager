import customtkinter as ctk
from src.api.client import api
import threading
import websocket
import json
from datetime import datetime
from tkinter import messagebox

class ChatView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT_FAMILY = "DejaVu Sans"
        
        # Quản lý trạng thái
        self.current_conv_id = None
        self.ws = None
        self.user_id = api.user_info.get("_id") if api.user_info else ""
        
        # Layout: 2 Cột (30% List - 70% Chat)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        # --- CỘT TRÁI: DANH SÁCH HỘI THOẠI ---
        self.left_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        # Header cột trái
        ctk.CTkLabel(self.left_frame, text="Messages", font=(self.FONT_FAMILY, 18, "bold"), 
                     text_color="#334155").pack(pady=15, padx=15, anchor="w")
        
        # List User Scrollable
        self.conv_list = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.conv_list.pack(fill="both", expand=True)

        # --- CỘT PHẢI: KHUNG CHAT ---
        self.right_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1) # Tin nhắn giãn nở
        self.right_frame.grid_columnconfigure(0, weight=1)

        # 1. Header người đang chat
        self.chat_header = ctk.CTkFrame(self.right_frame, height=50, fg_color="#F1F5F9", corner_radius=10)
        self.chat_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.lbl_chat_user = ctk.CTkLabel(self.chat_header, text="Select a conversation", 
                                          font=(self.FONT_FAMILY, 16, "bold"), text_color="#1E293B")
        self.lbl_chat_user.pack(side="left", padx=20, pady=10)

        # 2. Vùng hiển thị tin nhắn (Message Box)
        self.msg_box = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 3. Vùng nhập liệu (Input)
        self.input_area = ctk.CTkFrame(self.right_frame, height=60, fg_color="transparent")
        self.input_area.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.entry_msg = ctk.CTkEntry(self.input_area, placeholder_text="Type a message...", 
                                      font=(self.FONT_FAMILY, 14), height=40, border_width=1)
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda e: self.send_message()) # Enter để gửi

        self.btn_send = ctk.CTkButton(self.input_area, text="Send", width=80, height=40,
                                      fg_color="#3B82F6", hover_color="#2563EB",
                                      command=self.send_message)
        self.btn_send.pack(side="right")

        # --- KHỞI TẠO DỮ LIỆU ---
        self.load_conversations()
        self.connect_websocket()

    def connect_websocket(self):
        """Kết nối WebSocket để nhận tin nhắn Realtime"""
        # Lấy base url từ client nhưng đổi http -> ws
        ws_url = api.base_url.replace("http", "ws") + f"/ws/{self.user_id}"
        
        def on_message(ws, message):
            # Khi có tin nhắn mới từ Server gửi về
            data = json.loads(message)
            if data.get("event") == "new_message":
                msg_data = data["data"]
                # Nếu đang mở đúng cuộc hội thoại đó thì hiện lên ngay
                if msg_data["conversation_id"] == self.current_conv_id:
                    self.after(0, lambda: self.add_message_bubble(msg_data))

        def run_ws():
            self.ws = websocket.WebSocketApp(ws_url, on_message=on_message)
            self.ws.run_forever()

        # Chạy thread ngầm
        threading.Thread(target=run_ws, daemon=True).start()

    def load_conversations(self):
        convs = api.get_conversations()
        # Xóa cũ
        for widget in self.conv_list.winfo_children():
            widget.destroy()
            
        if not convs:
            ctk.CTkLabel(self.conv_list, text="No conversations yet").pack(pady=20)
            return

        # Render danh sách
        for conv in convs:
            # Logic tìm tên người kia (Không phải mình)
            # Tạm thời backend chưa trả về tên người kia trong list conv, 
            # mình sẽ lấy User ID người kia làm tên tạm.
            # (Muốn xịn thì backend cần populate tên user)
            other_id = [pid for pid in conv["participants"] if pid != self.user_id]
            display_name = other_id[0] if other_id else "Unknown"
            
            btn = ctk.CTkButton(self.conv_list, text=f" 👤 {display_name}", 
                                fg_color="transparent", text_color="#1E293B",
                                hover_color="#E2E8F0", anchor="w", height=50,
                                font=(self.FONT_FAMILY, 14),
                                command=lambda c=conv: self.select_conversation(c))
            btn.pack(fill="x", pady=2)

    def select_conversation(self, conv):
        self.current_conv_id = conv["_id"]
        
        # Update Header
        other_id = [pid for pid in conv["participants"] if pid != self.user_id]
        name = other_id[0] if other_id else "Unknown"
        self.lbl_chat_user.configure(text=f"Chat with {name}")

        # Load lịch sử
        self.msg_box.destroy() # Reset frame tin nhắn để xóa sạch cũ
        self.msg_box = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        threading.Thread(target=self.load_history).start()

    def load_history(self):
        msgs = api.get_messages(self.current_conv_id)
        self.after(0, lambda: self.render_messages(msgs))

    def render_messages(self, msgs):
        for msg in msgs:
            self.add_message_bubble(msg)
        # Cuộn xuống cuối
        self.msg_box._parent_canvas.yview_moveto(1.0)

    def add_message_bubble(self, msg):
        is_me = (msg["sender_id"] == self.user_id)
        
        # Frame bao quanh tin nhắn
        bubble_frame = ctk.CTkFrame(self.msg_box, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5, padx=10)

        # Style bong bóng
        bg_color = "#3B82F6" if is_me else "#E2E8F0" # Xanh nếu là mình, Xám nếu là họ
        text_color = "white" if is_me else "black"
        anchor = "e" if is_me else "w" # Căn phải nếu là mình
        
        # Nội dung tin nhắn
        # Dùng Label bo tròn (corner_radius)
        lbl = ctk.CTkLabel(bubble_frame, text=msg["content"], 
                           fg_color=bg_color, text_color=text_color,
                           corner_radius=15, padx=15, pady=8,
                           font=(self.FONT_FAMILY, 13), wraplength=400) # Tự xuống dòng
        lbl.pack(side="right" if is_me else "left")

    def send_message(self):
        text = self.entry_msg.get()
        if not text or not self.current_conv_id: return
        
        # Gửi qua WebSocket (Gửi JSON)
        # Backend mong đợi: {"conversation_id": "...", "content": "..."}
        payload = {
            "conversation_id": self.current_conv_id,
            "content": text
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(payload))
            self.entry_msg.delete(0, "end")
            # UI sẽ tự update khi nhận lại tin nhắn từ server (on_message)
            # Nhưng để mượt hơn, ta có thể add luôn vào UI (Optimistic UI)
            # self.add_message_bubble(...) 
        else:
            messagebox.showerror("Error", "Lost connection to chat server")

    def destroy(self):
        # Đóng socket khi tắt màn hình chat
        if self.ws:
            self.ws.close()
        super().destroy()