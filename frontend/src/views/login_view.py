import customtkinter as ctk
from PIL import Image
from src.api.client import api
import threading
import os

class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        
        self.configure(fg_color="white")

        # --- FIX LAYOUT ---
        self.grid_columnconfigure(0, weight=1, uniform="group1") 
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        # ============================================================
        # CỘT TRÁI: HÌNH ẢNH
        # ============================================================
        self.image_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_frame.grid_propagate(False) 

        # Load ảnh bìa
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(current_dir, "../../assets/login.jpeg") 
        self.original_image = None

        try:
            self.original_image = Image.open(self.img_path)
        except Exception as e:
            print(f"Error loading image: {e}")

        self.image_label = ctk.CTkLabel(self.image_frame, text="")
        self.image_label.place(x=0, y=0, relwidth=1, relheight=1) 
        self.image_frame.bind("<Configure>", self.resize_image)

        # ============================================================
        # CỘT PHẢI: FORM LOGIN
        # ============================================================
        self.frame_form = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.frame_form.grid(row=0, column=1, sticky="nsew")
        
        self.center_box = ctk.CTkFrame(self.frame_form, fg_color="white")
        self.center_box.place(relx=0.5, rely=0.5, anchor="center")

        # Font Config
        FONT_FAMILY = "DejaVu Sans"
        
        TITLE_FONT = (FONT_FAMILY, 39, "bold")
        DESC_FONT = (FONT_FAMILY, 18)
        LABEL_FONT = (FONT_FAMILY, 16, "bold")
        INPUT_FONT = (FONT_FAMILY, 15)
        BTN_FONT = (FONT_FAMILY, 18, "bold")

        # 1. Title
        ctk.CTkLabel(self.center_box, text="Welcome Back!", 
                     font=TITLE_FONT, text_color="black", 
                     fg_color="white").pack(pady=(0, 10), anchor="w")
        
        ctk.CTkLabel(self.center_box, text="Sign in to continue to SMS", 
                     font=DESC_FONT, text_color="#555",
                     fg_color="white").pack(pady=(0, 50), anchor="w")

        # 2. Input ID
        ctk.CTkLabel(self.center_box, text="Student ID", 
                     font=LABEL_FONT, text_color="#111",
                     fg_color="white").pack(anchor="w", pady=(0, 10))
        
        self.entry_user = ctk.CTkEntry(self.center_box, width=360, height=55, 
                                       placeholder_text="Ex: B19DCCN001",
                                       border_width=2, corner_radius=12,
                                       fg_color="#F8F9FA", border_color="#D1D5DB",
                                       text_color="black", font=INPUT_FONT)
        self.entry_user.pack(pady=(0, 25))

        # 3. Input Password
        ctk.CTkLabel(self.center_box, text="Password", 
                     font=LABEL_FONT, text_color="#111",
                     fg_color="white").pack(anchor="w", pady=(0, 10))
                     
        self.entry_pass = ctk.CTkEntry(self.center_box, width=360, height=55, 
                                       placeholder_text="••••••••", show="*",
                                       border_width=2, corner_radius=12,
                                       fg_color="#F8F9FA", border_color="#D1D5DB",
                                       text_color="black", font=INPUT_FONT)
        self.entry_pass.pack(pady=(0, 20))

        # --- LOAD ICON SHOW/HIDE PASSWORD ---
        self.icon_eye = None
        self.icon_eye_off = None
        try:
            # Đường dẫn tới folder icons
            icon_dir = os.path.join(current_dir, "../../assets/icons")
            # Load và resize icon nhỏ vừa vặn (20x20)
            self.icon_eye = ctk.CTkImage(Image.open(os.path.join(icon_dir, "hide.png")), size=(20, 20))
            self.icon_eye_off = ctk.CTkImage(Image.open(os.path.join(icon_dir, "visible.png")), size=(20, 20))
        except Exception as e:
            print(f"Warning: Missing eye icons in assets/icons/. Error: {e}")

        # --- NÚT ICON ---
        self.is_password_visible = False
        
        # Mặc định là ẩn -> Hiện icon eye_off (gạch chéo)
        # Nếu không tải được ảnh thì nó sẽ hiện nút trống (vẫn bấm được)
        self.btn_show_pass = ctk.CTkButton(self.entry_pass, text="", width=40, height=30,
                                           image=self.icon_eye_off, # Icon mặc định
                                           fg_color="transparent", hover_color="#E5E7EB",
                                           command=self.toggle_password_visibility)
        
        self.btn_show_pass.place(relx=1.0, rely=0.5, anchor="e", x=-10)

        # 4. Options
        self.frame_opts = ctk.CTkFrame(self.center_box, fg_color="white")
        self.frame_opts.pack(fill="x", pady=(0, 40))
        
        self.chk_remember = ctk.CTkCheckBox(self.frame_opts, text="Remember me", 
                                            font=(FONT_FAMILY, 16), text_color="#333",
                                            fg_color="#3B8ED0", hover_color="#36719F",
                                            border_color="#888", border_width=2,
                                            checkbox_width=24, checkbox_height=24)
        self.chk_remember.pack(side="left")
        
        self.btn_forgot = ctk.CTkButton(self.frame_opts, text="Forgot password?", 
                                        fg_color="white", text_color="#3B8ED0", 
                                        font=(FONT_FAMILY, 16, "bold"), hover=False, width=100)
        self.btn_forgot.pack(side="right")

        # 5. Login Button
        self.btn_login = ctk.CTkButton(self.center_box, text="Login", width=360, height=60,
                                       font=BTN_FONT, corner_radius=12,
                                       fg_color="#3B8ED0", hover_color="#2980b9",
                                       command=self.handle_login)
        self.btn_login.pack(pady=(0, 20))

        # 6. Error
        self.lbl_error = ctk.CTkLabel(self.center_box, text="", text_color="#E74C3C", 
                                      font=(FONT_FAMILY, 14), fg_color="white")
        self.lbl_error.pack()

    def toggle_password_visibility(self):
        """Đổi icon và thuộc tính show"""
        if self.is_password_visible:
            # Đang hiện -> Chuyển sang Ẩn
            self.entry_pass.configure(show="*")
            # Khi ẩn: Hiện icon gạch chéo (để báo hiệu bấm vào sẽ hiện)
            # Hoặc tùy logic bạn thích (thường ẩn thì hiện icon mắt gạch)
            self.btn_show_pass.configure(image=self.icon_eye_off) 
            self.is_password_visible = False
        else:
            # Đang ẩn -> Chuyển sang Hiện
            self.entry_pass.configure(show="") 
            self.btn_show_pass.configure(image=self.icon_eye) # Hiện icon mắt mở
            self.is_password_visible = True

    def resize_image(self, event):
        if not self.original_image: return
        new_width = event.width
        new_height = event.height
        if new_width < 10 or new_height < 10: return

        img_ratio = self.original_image.width / self.original_image.height
        frame_ratio = new_width / new_height

        if frame_ratio > img_ratio:
            resize_width = new_width
            resize_height = int(resize_width / img_ratio)
        else:
            resize_height = new_height
            resize_width = int(resize_height * img_ratio)

        try:
            resized = self.original_image.resize((resize_width, resize_height), Image.LANCZOS)
            left = (resize_width - new_width) / 2
            top = (resize_height - new_height) / 2
            right = (resize_width + new_width) / 2
            bottom = (resize_height + new_height) / 2
            cropped = resized.crop((left, top, right, bottom))
            
            ctk_image = ctk.CTkImage(light_image=cropped, dark_image=cropped, 
                                     size=(new_width, new_height))
            self.image_label.configure(image=ctk_image)
        except:
            pass

    def handle_login(self):
        mssv = self.entry_user.get()
        pwd = self.entry_pass.get()

        if not mssv or not pwd:
            self.lbl_error.configure(text="Please enter your ID and Password")
            return

        self.btn_login.configure(state="disabled", text="Verifying...")
        self.lbl_error.configure(text="")
        threading.Thread(target=lambda: self.run_login_thread(mssv, pwd)).start()

    def run_login_thread(self, mssv, pwd):
        success, msg = api.login(mssv, pwd)
        self.after(0, lambda: self.post_login(success, msg))

    def post_login(self, success, msg):
        self.btn_login.configure(state="normal", text="Login")
        if success:
            threading.Thread(target=lambda: api.get_user_info()).start()
            self.on_login_success()
        else:
            if "not found" in str(msg).lower(): msg = "User ID not found"
            if "password" in str(msg).lower(): msg = "Incorrect password"
            self.lbl_error.configure(text=f"{msg}")