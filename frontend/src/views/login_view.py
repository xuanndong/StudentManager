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

        # Layout 2 cột (50-50)
        self.grid_columnconfigure(0, weight=1, uniform="g") 
        self.grid_columnconfigure(1, weight=1, uniform="g")
        self.grid_rowconfigure(0, weight=1)

        # --- CỘT TRÁI: ẢNH ---
        self.img_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.img_frame.grid(row=0, column=0, sticky="nsew")
        self.img_frame.grid_propagate(False)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.img_path = os.path.join(current_dir, "../../assets/login.jpeg")
        self.original_img = None
        try: self.original_img = Image.open(self.img_path)
        except: pass
        
        self.img_lbl = ctk.CTkLabel(self.img_frame, text="")
        self.img_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        self.img_frame.bind("<Configure>", self.resize_img)

        # --- CỘT PHẢI: FORM ---
        self.form = ctk.CTkFrame(self, fg_color="white")
        self.form.grid(row=0, column=1, sticky="nsew")
        self.box = ctk.CTkFrame(self.form, fg_color="white")
        self.box.place(relx=0.5, rely=0.5, anchor="center")

        FONT = "Ubuntu"
        ctk.CTkLabel(self.box, text="Welcome Back!", font=(FONT, 32, "bold"), text_color="black").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self.box, text="Sign in to continue", font=(FONT, 16), text_color="gray").pack(anchor="w", pady=(0, 40))

        # Input User
        ctk.CTkLabel(self.box, text="Student ID / Account", font=(FONT, 14, "bold"), text_color="#333").pack(anchor="w", pady=(0, 5))
        self.user_ent = ctk.CTkEntry(self.box, width=340, height=50, font=(FONT, 14), border_width=1, border_color="#CCC")
        self.user_ent.pack(pady=(0, 20))

        # Input Password
        ctk.CTkLabel(self.box, text="Password", font=(FONT, 14, "bold"), text_color="#333").pack(anchor="w", pady=(0, 5))
        
        # Container ảo để chứa Entry (hoặc dùng chính Entry để place nút)
        self.pass_ent = ctk.CTkEntry(self.box, width=340, height=50, show="*", font=(FONT, 14), border_width=1, border_color="#CCC")
        self.pass_ent.pack(pady=(0, 20))

        # --- ICON SHOW/HIDE PASSWORD ---
        self.icon_show = None
        self.icon_hide = None
        try:
            icon_dir = os.path.join(current_dir, "../../assets/icons")
            # Lưu ý: visible.png là mắt mở, hide.png là mắt đóng (hoặc gạch chéo)
            self.icon_show = ctk.CTkImage(Image.open(os.path.join(icon_dir, "visible.png")), size=(20, 20))
            self.icon_hide = ctk.CTkImage(Image.open(os.path.join(icon_dir, "hide.png")), size=(20, 20))
        except Exception as e:
            print(f"Warning load icons: {e}")

        self.is_pass_visible = False
        self.btn_eye = ctk.CTkButton(self.pass_ent, text="", width=30, height=30,
                                     image=self.icon_hide, # Mặc định là ẩn
                                     fg_color="transparent", hover_color="#EEEEEE",
                                     command=self.toggle_password)
        self.btn_eye.place(relx=1.0, rely=0.5, anchor="e", x=-10)

        # Login Button
        self.btn_login = ctk.CTkButton(self.box, text="Login", width=340, height=50, font=(FONT, 16, "bold"),
                                       fg_color="#3B82F6", hover_color="#2563EB", command=self.login)
        self.btn_login.pack(pady=10)
        
        self.lbl_err = ctk.CTkLabel(self.box, text="", text_color="red", font=(FONT, 12))
        self.lbl_err.pack()

    def toggle_password(self):
        if self.is_pass_visible:
            # Đang hiện -> Chuyển sang Ẩn
            self.pass_ent.configure(show="*")
            self.btn_eye.configure(image=self.icon_hide)
            self.is_pass_visible = False
        else:
            # Đang ẩn -> Chuyển sang Hiện
            self.pass_ent.configure(show="")
            self.btn_eye.configure(image=self.icon_show)
            self.is_pass_visible = True

    def resize_img(self, event):
        if not self.original_img or event.width < 10: return
        try:
            # Cover logic
            i_ratio = self.original_img.width / self.original_img.height
            f_ratio = event.width / event.height
            if f_ratio > i_ratio:
                w, h = event.width, int(event.width / i_ratio)
            else:
                h, w = event.height, int(event.height * i_ratio)
            resized = self.original_img.resize((w, h), Image.LANCZOS)
            left, top = (w - event.width)/2, (h - event.height)/2
            final = resized.crop((left, top, left + event.width, top + event.height))
            self.img_lbl.configure(image=ctk.CTkImage(final, size=(event.width, event.height)))
        except: pass

    def login(self):
        u, p = self.user_ent.get(), self.pass_ent.get()
        if not u or not p: return
        self.btn_login.configure(state="disabled", text="Verifying...")
        threading.Thread(target=lambda: self.run_login(u, p)).start()

    def run_login(self, u, p):
        ok, msg = api.login(u, p)
        self.after(0, lambda: self.post_login(ok, msg))

    def post_login(self, ok, msg):
        self.btn_login.configure(state="normal", text="Login")
        if ok:
            threading.Thread(target=api.get_user_info).start()
            self.on_login_success()
        else:
            self.lbl_err.configure(text=msg)