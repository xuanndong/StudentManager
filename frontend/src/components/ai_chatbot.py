import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox


class AIChatbot(ctk.CTkToplevel):
    """AI Assistant Chatbot Window"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("AI Assistant")
        self.geometry("500x700")
        self.configure(fg_color="white")
        
        self.FONT_FAMILY = "Ubuntu"
        self._destroyed = False
        
        self.build_ui()
    
    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#6366F1", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="AI Assistant", 
                    font=(self.FONT_FAMILY, 18, "bold"),
                    text_color="white").pack(side="left", padx=20, pady=15)
        
        # Close button
        ctk.CTkButton(header, text="", width=30, height=30,
                     fg_color="transparent", hover_color="#5558E3",
                     command=self.destroy).pack(side="right", padx=10)
        
        # Welcome message
        welcome_frame = ctk.CTkFrame(self, fg_color="#EEF2FF", corner_radius=0)
        welcome_frame.pack(fill="x", padx=0, pady=0)
        
        user_role = api.user_info.get('role', 'STUDENT') if api.user_info else 'STUDENT'
        role_messages = {
            'STUDENT': 'Tôi có thể giúp bạn về học tập, điểm số, và lời khuyên học tập!',
            'TEACHER': 'Tôi có thể hỗ trợ bạn về quản lý lớp học và phương pháp giảng dạy!',
            'CVHT': 'Tôi có thể giúp bạn theo dõi sinh viên và lập kế hoạch học tập!',
            'ADMIN': 'Tôi có thể hỗ trợ bạn về quản lý hệ thống!'
        }
        
        ctk.CTkLabel(welcome_frame, 
                    text=f"Xin chào! {role_messages.get(user_role, 'Tôi có thể giúp gì cho bạn?')}",
                    font=(self.FONT_FAMILY, 12),
                    text_color="#4338CA",
                    wraplength=450).pack(padx=20, pady=15)
        
        # Chat messages area
        self.messages_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.messages_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add initial bot message
        self.add_bot_message("Xin chào! Tôi là trợ lý AI. Bạn có câu hỏi gì không?")
        
        # Input area
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.input_entry = ctk.CTkEntry(input_frame, 
                                        placeholder_text="Nhập câu hỏi của bạn...",
                                        font=(self.FONT_FAMILY, 13),
                                        height=45)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = ctk.CTkButton(input_frame, text="Gửi", width=80, height=45,
                                      fg_color="#6366F1", hover_color="#5558E3",
                                      font=(self.FONT_FAMILY, 13, "bold"),
                                      command=self.send_message)
        self.send_btn.pack(side="right")
    
    def add_user_message(self, text):
        """Add user message bubble"""
        if self._destroyed:
            return
        
        bubble = ctk.CTkFrame(self.messages_frame, fg_color="#6366F1", corner_radius=15)
        bubble.pack(anchor="e", pady=5, padx=10)
        
        ctk.CTkLabel(bubble, text=text, font=(self.FONT_FAMILY, 12),
                    text_color="white", wraplength=350,
                    justify="left").pack(padx=15, pady=10)
    
    def add_bot_message(self, text):
        """Add bot message bubble"""
        if self._destroyed:
            return
        
        bubble = ctk.CTkFrame(self.messages_frame, fg_color="#F1F5F9", corner_radius=15)
        bubble.pack(anchor="w", pady=5, padx=10)
        
        ctk.CTkLabel(bubble, text=text, font=(self.FONT_FAMILY, 12),
                    text_color="#334155", wraplength=350,
                    justify="left").pack(padx=15, pady=10)
    
    def add_loading_message(self):
        """Add loading indicator"""
        if self._destroyed:
            return
        
        loading = ctk.CTkFrame(self.messages_frame, fg_color="#F1F5F9", corner_radius=15)
        loading.pack(anchor="w", pady=5, padx=10)
        
        ctk.CTkLabel(loading, text="Đang suy nghĩ...", font=(self.FONT_FAMILY, 12, "italic"),
                    text_color="#94A3B8").pack(padx=15, pady=10)
        
        return loading
    
    def send_message(self):
        """Send message to AI"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        # Add user message
        self.add_user_message(message)
        self.input_entry.delete(0, "end")
        
        # Disable input while processing
        self.send_btn.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        
        # Add loading
        loading = self.add_loading_message()
        
        # Send to API in background
        def send_to_api():
            response = api.chat_with_ai(message)
            
            if not self._destroyed:
                self.after(0, lambda: self.handle_response(response, loading))
        
        threading.Thread(target=send_to_api, daemon=True).start()
    
    def handle_response(self, response, loading_widget):
        """Handle AI response"""
        if self._destroyed:
            return
        
        # Remove loading
        try:
            loading_widget.destroy()
        except:
            pass
        
        # Add bot response
        if response:
            self.add_bot_message(response)
        else:
            self.add_bot_message("Xin lỗi, tôi không thể trả lời lúc này. Vui lòng thử lại.")
        
        # Re-enable input
        self.send_btn.configure(state="normal")
        self.input_entry.configure(state="normal")
        self.input_entry.focus()
        
        # Scroll to bottom
        try:
            self.messages_frame._parent_canvas.yview_moveto(1.0)
        except:
            pass
    
    def destroy(self):
        self._destroyed = True
        super().destroy()
