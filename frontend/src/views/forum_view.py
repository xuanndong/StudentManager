import customtkinter as ctk
from src.api.client import api
import threading
from datetime import datetime
from tkinter import messagebox

class ForumView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT_FAMILY = "DejaVu Sans"
        self.user_id = api.user_info.get("_id")
        self.selected_class_id = None

        # Layout: 2 Cột (25% Danh sách lớp - 75% Newsfeed)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- CỘT TRÁI: DANH SÁCH LỚP ---
        self.left_panel = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.left_panel, text="Select Class", 
                     font=(self.FONT_FAMILY, 16, "bold"), text_color="#334155").pack(pady=15)
        
        self.class_list = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.class_list.pack(fill="both", expand=True)

        # --- CỘT PHẢI: NEWSFEED ---
        self.feed_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.feed_panel.grid(row=0, column=1, sticky="nsew")
        
        # Header của Feed (Nút đăng bài)
        self.feed_header = ctk.CTkFrame(self.feed_panel, fg_color="white", corner_radius=10, height=60)
        self.feed_header.pack(fill="x", pady=(0, 10))
        self.feed_header.pack_propagate(False) # Giữ chiều cao cố định

        self.btn_new_post = ctk.CTkButton(self.feed_header, text="+ New Post", 
                                          font=(self.FONT_FAMILY, 14, "bold"),
                                          fg_color="#3B82F6", hover_color="#2563EB",
                                          state="disabled", # Chỉ enable khi chọn lớp
                                          command=self.open_post_dialog)
        self.btn_new_post.pack(side="right", padx=20, pady=10)
        
        self.lbl_current_class = ctk.CTkLabel(self.feed_header, text="Please select a class", 
                                              font=(self.FONT_FAMILY, 16, "bold"), text_color="#475569")
        self.lbl_current_class.pack(side="left", padx=20)

        # Khu vực hiển thị bài viết (Scrollable)
        self.posts_area = ctk.CTkScrollableFrame(self.feed_panel, fg_color="transparent")
        self.posts_area.pack(fill="both", expand=True)

        # Load dữ liệu
        threading.Thread(target=self.load_classes).start()

    def load_classes(self):
        classes = api.get_my_classes()
        self.after(0, lambda: self.render_class_list(classes))

    def render_class_list(self, classes):
        for widget in self.class_list.winfo_children(): widget.destroy()
        
        if not classes:
            ctk.CTkLabel(self.class_list, text="No classes joined").pack(pady=10)
            return

        for cls in classes:
            btn = ctk.CTkButton(self.class_list, text=cls['name'], 
                                fg_color="transparent", text_color="#334155",
                                hover_color="#F1F5F9", anchor="w", height=40,
                                font=(self.FONT_FAMILY, 13),
                                command=lambda c=cls: self.select_class(c))
            btn.pack(fill="x", pady=2)

    def select_class(self, class_data):
        self.selected_class_id = class_data['_id']
        self.lbl_current_class.configure(text=class_data['name'])
        self.btn_new_post.configure(state="normal")
        
        # Clear feed cũ
        for widget in self.posts_area.winfo_children(): widget.destroy()
        
        # Hiện loading
        loading = ctk.CTkLabel(self.posts_area, text="Loading posts...", text_color="gray")
        loading.pack(pady=20)
        
        threading.Thread(target=lambda: self.load_posts(loading)).start()

    def load_posts(self, loading_widget):
        posts = api.get_class_posts(self.selected_class_id)
        self.after(0, lambda: self.render_posts(posts, loading_widget))

    def render_posts(self, posts, loading_widget):
        loading_widget.destroy()
        
        if not posts:
            ctk.CTkLabel(self.posts_area, text="No posts yet. Be the first to share!", 
                         font=(self.FONT_FAMILY, 14)).pack(pady=20)
            return

        for post in posts:
            self.create_post_card(post)

    def create_post_card(self, post):
        """Tạo giao diện 1 bài viết (Card)"""
        card = ctk.CTkFrame(self.posts_area, fg_color="white", corner_radius=10)
        card.pack(fill="x", pady=10, padx=5)

        # 1. Header: Author + Time
        header = ctk.CTkFrame(card, fg_color="transparent", height=30)
        header.pack(fill="x", padx=15, pady=(10, 5))
        
        # Avatar giả
        author_id = post.get('author_id', 'Unknown')
        ctk.CTkLabel(header, text="👤", font=("Arial", 16)).pack(side="left")
        ctk.CTkLabel(header, text=f" {author_id}", font=(self.FONT_FAMILY, 13, "bold"), 
                     text_color="#1E293B").pack(side="left")
        
        # Thời gian (Format đơn giản)
        time_str = post.get('created_at', '')[:10] # Lấy ngày YYYY-MM-DD
        ctk.CTkLabel(header, text=time_str, font=(self.FONT_FAMILY, 11), 
                     text_color="gray").pack(side="right")

        # 2. Content
        content = ctk.CTkLabel(card, text=post['content'], anchor="w", justify="left",
                               font=(self.FONT_FAMILY, 14), text_color="#334155",
                               wraplength=600) # Tự xuống dòng
        content.pack(fill="x", padx=20, pady=5)

        # 3. Actions (Like & Stats)
        actions = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=0, height=40)
        actions.pack(fill="x", pady=(10, 0))
        
        # Check xem mình đã like chưa
        is_liked = self.user_id in post.get('likes', [])
        like_color = "#EF4444" if is_liked else "#64748B"
        like_text = "❤️ Liked" if is_liked else "🤍 Like"
        
        btn_like = ctk.CTkButton(actions, text=f"{like_text} ({len(post.get('likes', []))})", 
                                 fg_color="transparent", hover_color="#E2E8F0",
                                 text_color=like_color, width=80,
                                 font=(self.FONT_FAMILY, 12, "bold"),
                                 command=lambda p=post: self.toggle_like_ui(p))
        btn_like.pack(side="left", padx=10, pady=5)

        # 4. Comments Section
        comments_frame = ctk.CTkFrame(card, fg_color="#F1F5F9", corner_radius=0)
        comments_frame.pack(fill="x")

        # List comments cũ
        for cmt in post.get('comments', []):
            cmt_row = ctk.CTkFrame(comments_frame, fg_color="transparent")
            cmt_row.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(cmt_row, text=f"{cmt.get('user_id', 'User')}: ", 
                         font=(self.FONT_FAMILY, 12, "bold"), text_color="#334155").pack(side="left")
            ctk.CTkLabel(cmt_row, text=cmt.get('content', ''), 
                         font=(self.FONT_FAMILY, 12)).pack(side="left")

        # Input Comment
        input_row = ctk.CTkFrame(comments_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=5)
        
        entry_cmt = ctk.CTkEntry(input_row, placeholder_text="Write a comment...", height=30, border_width=1)
        entry_cmt.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Hàm gửi comment (Closure để giữ biến post_id)
        def send_comment(pid=post['_id'], ent=entry_cmt):
            content = ent.get()
            if content:
                api.add_comment(pid, content)
                ent.delete(0, "end")
                # Reload lại post này hoặc refresh cả list (đơn giản nhất là refresh list)
                self.load_posts(ctk.CTkLabel(self.posts_area, text="Refreshing..."))

        btn_send = ctk.CTkButton(input_row, text="➤", width=40, height=30, 
                                 fg_color="#3B82F6", command=send_comment)
        btn_send.pack(side="right")
        entry_cmt.bind("<Return>", lambda e: send_comment())

    def toggle_like_ui(self, post):
        # Gọi API
        api.toggle_like(post['_id'])
        # Refresh UI (Reload feed)
        # Để mượt hơn có thể chỉ update nút, nhưng reload là cách an toàn nhất
        self.load_posts(ctk.CTkLabel(self.posts_area, text=""))

    def open_post_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Post")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        ctk.CTkLabel(dialog, text="Create Post", font=(self.FONT_FAMILY, 18, "bold"), text_color="#333").pack(pady=15)
        
        txt_content = ctk.CTkTextbox(dialog, width=350, height=150, border_width=1)
        txt_content.pack(pady=10)
        
        def submit():
            content = txt_content.get("1.0", "end").strip()
            if content:
                api.create_post(self.selected_class_id, content)
                dialog.destroy()
                self.load_posts(ctk.CTkLabel(self.posts_area, text="Updating..."))

        ctk.CTkButton(dialog, text="Post Now", width=350, command=submit).pack(pady=10)