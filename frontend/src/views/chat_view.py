import customtkinter as ctk
from src.api.client import api
import threading
import websocket
import json
from tkinter import messagebox

class ChatView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT_FAMILY = "Ubuntu"
        
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
        header_left = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        header_left.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(header_left, text="Messages", font=(self.FONT_FAMILY, 18, "bold"), 
                     text_color="#334155").pack(side="left")
        
        ctk.CTkButton(header_left, text="+ New", width=60, height=30,
                     fg_color="#10B981", hover_color="#059669",
                     command=self.new_conversation_dialog).pack(side="right")
        
        # List User Scrollable
        self.conv_list = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.conv_list.pack(fill="both", expand=True)

        # --- CỘT PHẢI: KHUNG CHAT ---
        self.right_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1) # Tin nhắn giãn nở
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Header người đang chat
        self.chat_header = ctk.CTkFrame(self.right_frame, height=50, fg_color="#F1F5F9", corner_radius=10)
        self.chat_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.lbl_chat_user = ctk.CTkLabel(self.chat_header, text="Select a conversation", 
                                          font=(self.FONT_FAMILY, 16, "bold"), text_color="#1E293B")
        self.lbl_chat_user.pack(side="left", padx=20, pady=10)

        # Vùng hiển thị tin nhắn (Message Box)
        self.msg_box = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Vùng nhập liệu (Input)
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
        self._destroyed = False
        
        def on_message(ws, message):
            # Khi có tin nhắn mới từ Server gửi về
            try:
                data = json.loads(message)
                if data.get("event") == "new_message":
                    msg_data = data["data"]
                    # Nếu đang mở đúng cuộc hội thoại đó thì hiện lên ngay
                    if msg_data["conversation_id"] == self.current_conv_id and not self._destroyed:
                        try:
                            self.after(0, lambda: self.add_message_bubble(msg_data) if not self._destroyed else None)
                        except:
                            pass  # Widget destroyed
            except:
                pass  # Ignore errors in callback

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
        
        # Filter: Chỉ hiển thị conversations có tin nhắn
        convs_with_messages = [c for c in convs if c.get("last_message")]
            
        if not convs_with_messages:
            ctk.CTkLabel(self.conv_list, text="No conversations yet\nClick + New to start chatting").pack(pady=20)
            return

        # Render danh sách
        for conv in convs_with_messages:
            # Get other user name from populated field
            display_name = conv.get("other_user_name", "Unknown")
            
            # Check if has unread messages (simple: check if last message sender is not me)
            last_msg = conv.get("last_message")
            has_unread = False
            if last_msg and last_msg.get("sender_id") != self.user_id:
                has_unread = True
            
            # Add red dot if unread
            display_text = f"{display_name}" if has_unread else f"{display_name}"
            
            btn = ctk.CTkButton(self.conv_list, text=display_text, 
                                fg_color="transparent", text_color="#1E293B",
                                hover_color="#E2E8F0", anchor="w", height=50,
                                font=(self.FONT_FAMILY, 14),
                                command=lambda c=conv: self.select_conversation(c))
            btn.pack(fill="x", pady=2)

    def select_conversation(self, conv):
        self.current_conv_id = conv["_id"]
        
        # Update Header with populated name
        name = conv.get("other_user_name", "Unknown")
        self.lbl_chat_user.configure(text=f"Chat with {name}")

        # Load lịch sử
        self.msg_box.destroy() # Reset frame tin nhắn để xóa sạch cũ
        self.msg_box = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        threading.Thread(target=self.load_history, daemon=True).start()

    def load_history(self):
        msgs = api.get_messages(self.current_conv_id)
        if not self._destroyed:
            try:
                self.after(0, lambda: self.render_messages(msgs) if not self._destroyed else None)
            except:
                pass  # Widget destroyed

    def render_messages(self, msgs):
        if self._destroyed:
            return
        for msg in msgs:
            self.add_message_bubble(msg)
        # Cuộn xuống cuối
        try:
            self.msg_box._parent_canvas.yview_moveto(1.0)
        except:
            pass  # Widget destroyed

    def add_message_bubble(self, msg):
        if self._destroyed:
            return
            
        is_me = (msg["sender_id"] == self.user_id)
        
        try:
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
        except:
            pass  # Widget destroyed

    def send_message(self):
        text = self.entry_msg.get()
        if not text or not self.current_conv_id: return
        
        # Gửi qua WebSocket (Gửi JSON)
        payload = {
            "conversation_id": self.current_conv_id,
            "content": text
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(payload))
            self.entry_msg.delete(0, "end")
        else:
            messagebox.showerror("Error", "Lost connection to chat server")

    def new_conversation_dialog(self):
        """Dialog để chọn người chat - bao gồm classmates, teachers, CVHT"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Conversation")
        dialog.geometry("500x650")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        # Header
        ctk.CTkLabel(dialog, text="Start a new conversation", 
                    font=(self.FONT_FAMILY, 16, "bold"), 
                    text_color="#1E293B").pack(pady=15)
        
        # Check user role
        user_role = api.user_info.get('role') if api.user_info else None
        
        # Tab selector - only show classmates for non-ADMIN
        if user_role != "ADMIN":
            tab_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            tab_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            selected_tab = ctk.StringVar(value="classmates")
            
            ctk.CTkRadioButton(tab_frame, text="My Classmates", variable=selected_tab, 
                              value="classmates", font=(self.FONT_FAMILY, 12)).pack(side="left", padx=10)
            ctk.CTkRadioButton(tab_frame, text="Search by Phone", variable=selected_tab, 
                              value="phone", font=(self.FONT_FAMILY, 12)).pack(side="left", padx=10)
        else:
            # ADMIN only has phone search
            selected_tab = ctk.StringVar(value="phone")
        
        # Loading
        loading = ctk.CTkLabel(dialog, text="Loading...", text_color="#94A3B8")
        loading.pack(pady=20)
        
        # Get classmates (only for non-ADMIN)
        classmates = []
        if user_role != "ADMIN":
            admin_classes = api.get_my_administrative_classes()
            if admin_classes:
                class_id = admin_classes[0].get('id', admin_classes[0].get('_id'))
                classmates = api.get_administrative_class_students(class_id)
        
        loading.destroy()
        
        # Search box
        search_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, 
                                    placeholder_text="Search by name or phone...",
                                    textvariable=search_var,
                                    height=35)
        search_entry.pack(fill="x")
        
        # List frame
        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        def render_users(filter_text="", tab="classmates"):
            # Clear list
            for widget in list_frame.winfo_children():
                widget.destroy()
            
            # Select user list based on tab
            if tab == "classmates":
                users = classmates
                # Filter classmates by name or phone
                filtered = [u for u in users 
                           if filter_text.lower() in u.get('full_name', '').lower() 
                           or filter_text in u.get('phone', '')]
            else:  # phone search - search via API
                if not filter_text:
                    ctk.CTkLabel(list_frame, text="Enter phone number to search\n(Example: 0987654321 for CVHT)",
                                font=(self.FONT_FAMILY, 12), 
                                text_color="#94A3B8").pack(pady=30)
                    return
                
                # Search via API - no additional filtering needed
                user = api.search_user_by_phone(filter_text)
                filtered = [user] if user else []
            
            # Exclude self
            current_user_id = api.user_info.get("_id")
            filtered = [u for u in filtered if u.get('_id') != current_user_id]
            
            if not filtered:
                no_result_text = "No classmates found" if tab == "classmates" else "No user found with that phone"
                ctk.CTkLabel(list_frame, text=no_result_text,
                            font=(self.FONT_FAMILY, 12), 
                            text_color="#94A3B8").pack(pady=20)
                return
            
            for user in filtered:
                # Click handler - create conversation and open chat
                def start_chat(u=user):
                    phone = u.get('phone')
                    if not phone:
                        messagebox.showerror("Error", "User has no phone number")
                        return
                    
                    # Create conversation
                    conv = api.create_conversation_by_phone(phone)
                    if conv:
                        # Manually add user info to conv since backend might not populate for new conv
                        conv["other_user_name"] = u.get("full_name", "Unknown")
                        conv["other_user_phone"] = u.get("phone", "")
                        
                        dialog.destroy()
                        self.load_conversations()
                        self.select_conversation(conv)
                    else:
                        messagebox.showerror("Error", "Failed to create conversation")
                
                # Simple display: Name (ROLE)
                name_role = f"{user.get('full_name', 'Unknown')} ({user.get('role', 'USER')})"
                
                btn = ctk.CTkButton(list_frame, text=name_role,
                                   fg_color="#F8FAFC", hover_color="#E2E8F0",
                                   text_color="#334155", anchor="w",
                                   font=(self.FONT_FAMILY, 13),
                                   height=45, corner_radius=8,
                                   command=start_chat)
                btn.pack(fill="x", pady=2)
        
        # Initial render
        render_users("", selected_tab.get())
        
        # Update on tab change or search
        def on_change(*args):
            render_users(search_var.get(), selected_tab.get())
        
        search_var.trace_add("write", on_change)
        selected_tab.trace_add("write", on_change)

    def destroy(self):
        # Đóng socket khi tắt màn hình chat
        self._destroyed = True
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        super().destroy()