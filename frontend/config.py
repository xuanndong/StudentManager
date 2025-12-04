# src/config.py
import os
import sys
import customtkinter as ctk

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

APP_FONT_FAMILY = "Arial"  # Font dự phòng

def setup_app_resources():
    global APP_FONT_FAMILY
    
    font_relative = os.path.join("assets", "fonts", "AgaveNerdFont-Regular.ttf")
    
    font_path_absolute = get_resource_path(font_relative)

    if os.path.exists(font_path_absolute):
        try:
            ctk.FontManager.load_font(font_path_absolute)
            APP_FONT_FAMILY = "Agave Nerd Font"  # Tên font thật
            print(f"[Config] Đã load font: {APP_FONT_FAMILY}")
        except Exception as e:
            print(f"[Config] Lỗi load font: {e}")
    else:
        print(f"[Config] Không tìm thấy file font tại: {font_path_absolute}")