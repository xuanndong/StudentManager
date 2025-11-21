import customtkinter as ctk
from src.api.client import api
import threading

class ForumView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT_FAMILY = "Ubuntu"
        self.user_id = api.user_info.get("_id")
        self.selected_class_id = None
        self._destroyed = False

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
        threading.Thread(target=self.load_classes, daemon=True).start()

    def load_classes(self):
        classes = api.get_my_classes()
        if not self._destroyed:
            try:
                self.after(0, lambda: self.render_class_list(classes) if not self._destroyed else None)
            except:
                pass  # Widget destroyed

    def render_class_list(self, classes):
        for widget in self.class_list.winfo_children(): widget.destroy()
        
        if not classes:
            ctk.CTkLabel(self.class_list, text="No classes joined").pack(pady=10)
            return

        for cls in classes:
            # Xử lý cả administrative class và course class
            if 'name' in cls:
                # Administrative class
                display_name = cls['name']
            else:
                # Course class - hiển thị mã lớp
                display_name = f"{cls.get('semester', 'N/A')} - {cls.get('class_code', cls.get('group', 'N/A'))}"
            
            btn = ctk.CTkButton(self.class_list, text=display_name, 
                                fg_color="transparent", text_color="#334155",
                                hover_color="#F1F5F9", anchor="w", height=40,
                                font=(self.FONT_FAMILY, 13),
                                command=lambda c=cls: self.select_class(c))
            btn.pack(fill="x", pady=2)

    def select_class(self, class_data):
        # Lưu cả class data để biết loại class
        self.selected_class_data = class_data
        self.selected_class_id = class_data.get('id', class_data.get('_id'))
        
        # Display name
        if 'name' in class_data:
            display_name = class_data['name']
        else:
            display_name = f"{class_data.get('semester', 'N/A')} - {class_data.get('class_code', class_data.get('group', 'N/A'))}"
        
        self.lbl_current_class.configure(text=display_name)
        self.btn_new_post.configure(state="normal")
        
        # Clear feed cũ
        for widget in self.posts_area.winfo_children(): widget.destroy()
        
        # Hiện loading
        loading = ctk.CTkLabel(self.posts_area, text="Loading posts...", text_color="gray")
        loading.pack(pady=20)
        
        threading.Thread(target=lambda: self.load_posts(loading)).start()

    def load_posts(self, loading_widget):
        if self._destroyed:
            return
            
        # Determine post type based on class data
        if hasattr(self, 'selected_class_data'):
            if 'name' in self.selected_class_data:
                # Administrative class
                posts = api.get_administrative_posts(self.selected_class_id)
            else:
                # Course class
                posts = api.get_course_posts(self.selected_class_id)
        else:
            # Fallback to old method
            posts = api.get_class_posts(self.selected_class_id)
        
        if not self._destroyed:
            try:
                self.after(0, lambda: self.render_posts(posts, loading_widget) if not self._destroyed else None)
            except:
                pass  # Widget destroyed

    def render_posts(self, posts, loading_widget):
        if self._destroyed:
            return
        try:
            loading_widget.destroy()
        except:
            pass  # Already destroyed
        
        # Clear all existing posts first
        for widget in self.posts_area.winfo_children():
            widget.destroy()
        
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

        # Header: Author + Time
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        # Get author info - Ưu tiên từ backend populate
        author_id = post.get('author_id', 'Unknown')
        author_name = post.get('author_name')  # From backend populate
        author_role = post.get('author_role', '')  # From backend populate
        
        # Check if this is current user's post
        is_my_post = author_id == api.user_info.get("_id")
        
        # Nếu là bài của mình, hiển thị "You" thay vì tên
        if is_my_post:
            author_name = "You"
            if not author_role:
                author_role = api.user_info.get("role", "")
        elif not author_name or author_name == "Unknown":
            # Fallback nếu backend không populate và không phải bài của mình
            author_name = "Unknown User"
        
        # Avatar circle
        avatar = ctk.CTkFrame(header, width=36, height=36, corner_radius=18, fg_color="#DBEAFE")
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        
        # Initial - nếu là "You" thì dùng chữ Y
        if is_my_post and author_name == "You":
            initial = "Y"
        else:
            initial = author_name[0].upper() if author_name else "U"
        
        ctk.CTkLabel(avatar, text=initial, font=(self.FONT_FAMILY, 16, "bold"), 
                    text_color="#1D4ED8").place(relx=0.5, rely=0.5, anchor="center")
        
        # Name and role on same line
        name_frame = ctk.CTkFrame(header, fg_color="transparent")
        name_frame.pack(side="left", padx=10)
        
        # Format display text based on whether it's user's post
        if is_my_post:
            # Bài viết của mình: chỉ hiển thị "You"
            display_text = "You"
            role_color = "#0EA5E9"  # Màu xanh dương nổi bật
        else:
            # Bài viết người khác: "Full Name - ROLE"
            if author_role:
                role_colors = {"CVHT": "#D97706", "TEACHER": "#8B5CF6", "ADMIN": "#DC2626", "STUDENT": "#64748B"}
                role_color = role_colors.get(author_role, "#64748B")
                display_text = f"{author_name} - {author_role}"
            else:
                display_text = author_name
                role_color = "#1E293B"
        
        ctk.CTkLabel(name_frame, text=display_text, font=(self.FONT_FAMILY, 14, "bold"), 
                     text_color=role_color).pack(anchor="w")
        
        # Thời gian
        time_str = post.get('created_at', '')[:10] if isinstance(post.get('created_at'), str) else 'N/A'
        ctk.CTkLabel(header, text=time_str, font=(self.FONT_FAMILY, 11), 
                     text_color="#94A3B8").pack(side="right")

        # Content
        content = ctk.CTkLabel(card, text=post['content'], anchor="w", justify="left",
                               font=(self.FONT_FAMILY, 14), text_color="#334155",
                               wraplength=950)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Actions (Like & Stats)
        actions = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=0, height=40)
        actions.pack(fill="x", pady=(10, 0))
        
        is_liked = self.user_id in post.get('likes', [])
        like_color = "#EF4444" if is_liked else "#64748B"
        like_text = f"♥ Liked ({len(post.get('likes', []))})" if is_liked else f"♡ Like ({len(post.get('likes', []))})"
        
        btn_like = ctk.CTkButton(actions, text=like_text, 
                                 fg_color="transparent", hover_color="#E2E8F0",
                                 text_color=like_color, width=100,
                                 font=(self.FONT_FAMILY, 12, "bold"),
                                 command=lambda p=post, btn=None: self.toggle_like_ui(p, btn))
        btn_like.pack(side="left", padx=10, pady=5)
        
        # Update button reference sau khi tạo
        btn_like.configure(command=lambda p=post, btn=btn_like: self.toggle_like_ui(p, btn))

        # Comments Section
        comments_frame = ctk.CTkFrame(card, fg_color="#F1F5F9", corner_radius=0)
        comments_frame.pack(fill="x")

        # List comments cũ
        for cmt in post.get('comments', []):
            cmt_row = ctk.CTkFrame(comments_frame, fg_color="transparent")
            cmt_row.pack(fill="x", padx=15, pady=5)
            
            # Get commenter name
            commenter_id = cmt.get('user_id', 'Unknown')
            commenter_name = cmt.get('user_name')
            
            # Nếu là comment của mình, hiển thị "You"
            if commenter_id == api.user_info.get("_id"):
                commenter_name = "You"
            elif not commenter_name:
                # Fallback nếu backend không populate
                commenter_name = "Unknown User"
            
            # Comment bubble
            comment_bubble = ctk.CTkFrame(cmt_row, fg_color="#F1F5F9", corner_radius=8)
            comment_bubble.pack(fill="x", pady=2)
            
            ctk.CTkLabel(comment_bubble, text=commenter_name, 
                         font=(self.FONT_FAMILY, 11, "bold"), text_color="#0EA5E9").pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkLabel(comment_bubble, text=cmt.get('content', ''), 
                         font=(self.FONT_FAMILY, 12), text_color="#334155", 
                         wraplength=900, justify="left").pack(anchor="w", padx=10, pady=(0, 5))

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
                # Reload lại posts - tạo loading widget mới
                loading = ctk.CTkLabel(self.posts_area, text="Refreshing...")
                loading.pack(pady=20)
                threading.Thread(target=lambda: self.load_posts(loading)).start()

        btn_send = ctk.CTkButton(input_row, text="➤", width=40, height=30, 
                                 fg_color="#3B82F6", command=send_comment)
        btn_send.pack(side="right")
        entry_cmt.bind("<Return>", lambda e: send_comment())

    def toggle_like_ui(self, post, like_btn):
        """Toggle like và update UI ngay lập tức"""
        # Gọi API
        api.toggle_like(post['_id'])
        
        # Update UI ngay
        user_id = self.user_id
        likes = post.get('likes', [])
        
        if user_id in likes:
            # Unlike
            likes.remove(user_id)
            like_btn.configure(text=f"♡ Like ({len(likes)})", text_color="#64748B")
        else:
            # Like
            likes.append(user_id)
            like_btn.configure(text=f"♥ Liked ({len(likes)})", text_color="#EF4444")

    def open_post_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Post")
        dialog.geometry("450x320")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        
        ctk.CTkLabel(dialog, text="Create Post", font=(self.FONT_FAMILY, 18, "bold"), text_color="#333").pack(pady=15)
        
        txt_content = ctk.CTkTextbox(dialog, width=400, height=180, border_width=1, wrap="word")
        txt_content.pack(pady=10, padx=20)
        
        def submit():
            content = txt_content.get("1.0", "end").strip()
            if content:
                # Determine which API to call based on class type
                if hasattr(self, 'selected_class_data'):
                    if 'name' in self.selected_class_data:
                        # Administrative class
                        api.create_administrative_post(self.selected_class_id, content)
                    else:
                        # Course class
                        api.create_course_post(self.selected_class_id, content)
                else:
                    # Fallback
                    api.create_post(self.selected_class_id, content)
                
                dialog.destroy()
                # Reload posts properly
                loading = ctk.CTkLabel(self.posts_area, text="Updating...")
                loading.pack(pady=20)
                threading.Thread(target=lambda: self.load_posts(loading)).start()

        ctk.CTkButton(dialog, text="Post Now", width=400, height=40, 
                     fg_color="#3B82F6", command=submit).pack(pady=10, padx=20)
    
    def destroy(self):
        self._destroyed = True
        super().destroy()
