# main.py
import customtkinter as ctk
from src.views.login_view import LoginView
from src.views.main_view import MainView


# Cấu hình giao diện toàn cục
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Student Management System")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        # Khởi tạo container chính
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # Hiển thị màn hình login đầu tiên
        self.show_login()

    def show_login(self):
        self.clear_container()
        login_screen = LoginView(master=self.container, on_login_success=self.show_dashboard)
        login_screen.pack(fill="both", expand=True)

    def show_dashboard(self):
        self.clear_container()
        
        main_view = MainView(master=self.container, on_logout=self.show_login)
        main_view.pack(fill="both", expand=True)
        

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()