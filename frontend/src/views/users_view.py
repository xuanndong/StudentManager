import customtkinter as ctk
from src.api.client import api
import threading
from tkinter import messagebox

class UsersView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.FONT = "Ubuntu"
        
        # Modern header
        self.create_header()
        
        # Table container
        table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=16,
                                      border_width=1, border_color="#E2E8F0")
        table_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Table header
        self.table_header = ctk.CTkFrame(table_container, fg_color="#F8FAFC", corner_radius=0)
        self.table_header.pack(fill="x", padx=1, pady=1)
        
        cols = [("MSSV", 1.2), ("Full Name", 1.5), ("Email", 2), ("Role", 0.8), ("Status", 0.8), ("Actions", 1)]
        for col, weight in cols:
            ctk.CTkLabel(self.table_header, text=col, font=(self.FONT, 12, "bold"), 
                         text_color="#475569").pack(side="left", fill="x", expand=True, padx=10, pady=12)
        
        # Scrollable content
        self.scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent",
                                            scrollbar_button_color="#CBD5E1")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.refresh(None)

    def create_header(self):
        """Modern header with filters"""
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=16,
                             border_width=1, border_color="#E2E8F0")
        header.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkFrame(header, height=4, fg_color="#EF4444", corner_radius=16).pack(fill="x")
        
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="x", padx=25, pady=20)
        
        # Title
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, text="Group", font=(self.FONT, 28)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(title_frame, text="User Management", 
                    font=(self.FONT, 24, "bold"), text_color="#1E293B").pack(side="left")
        
        # Filters
        filter_frame = ctk.CTkFrame(content, fg_color="transparent")
        filter_frame.pack(side="right")
        
        ctk.CTkLabel(filter_frame, text="Filter by role:", 
                    font=(self.FONT, 12), text_color="#64748B").pack(side="left", padx=(0, 10))
        
        self.role_var = ctk.StringVar(value="ALL")
        self.cb_role = ctk.CTkComboBox(filter_frame, values=["ALL", "STUDENT", "CVHT", "ADMIN"],
                                       width=130, height=38, variable=self.role_var, 
                                       command=self.refresh, corner_radius=10,
                                       fg_color="#F8FAFC", border_color="#E2E8F0")
        self.cb_role.pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="↻", width=38, height=38,
                     fg_color="#6366F1", hover_color="#4F46E5",
                     corner_radius=10, font=(self.FONT, 16),
                     command=lambda: self.refresh(None)).pack(side="left", padx=5)

    def refresh(self, _):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        
        loading = ctk.CTkLabel(self.scroll, text="Loading...", text_color="gray")
        loading.pack(pady=20)
        
        threading.Thread(target=lambda: self.load(loading), daemon=True).start()

    def load(self, loading_lbl):
        role = None if self.role_var.get() == "ALL" else self.role_var.get()
        users = api.get_all_users(role)
        self.after(0, lambda: self.render(users, loading_lbl))

    def render(self, users, loading_lbl):
        loading_lbl.destroy()
        
        if not users:
            ctk.CTkLabel(self.scroll, text="No users found").pack(pady=20)
            return
        
        for user in users:
            self.add_row(user)

    def add_row(self, user):
        row = ctk.CTkFrame(self.scroll, fg_color="#FAFAFA", corner_radius=8)
        row.pack(fill="x", pady=4, padx=2)
        
        # MSSV
        ctk.CTkLabel(row, text=user['mssv'], font=(self.FONT, 12), 
                    text_color="#1E293B").pack(side="left", fill="x", expand=True, padx=10, pady=12)
        
        # Full Name
        ctk.CTkLabel(row, text=user.get('full_name', 'N/A'), font=(self.FONT, 12, "bold"), 
                    text_color="#334155").pack(side="left", fill="x", expand=True, padx=10)
        
        # Email
        ctk.CTkLabel(row, text=user['email'], font=(self.FONT, 11), 
                    text_color="#64748B").pack(side="left", fill="x", expand=True, padx=10)
        
        # Role badge
        role_colors = {"STUDENT": "#3B82F6", "CVHT": "#F59E0B", "ADMIN": "#EF4444"}
        role_bg = role_colors.get(user['role'], "#64748B")
        role_badge = ctk.CTkLabel(row, text=user['role'], font=(self.FONT, 10, "bold"),
                                 text_color="white", fg_color=role_bg, corner_radius=6)
        role_badge.pack(side="left", fill="x", expand=True, padx=10, ipadx=8, ipady=4)
        
        # Status badge
        is_active = user.get('is_active', True)
        status_text = "● Active" if is_active else "○ Inactive"
        status_color = "#10B981" if is_active else "#94A3B8"
        ctk.CTkLabel(row, text=status_text, font=(self.FONT, 11, "bold"), 
                    text_color=status_color).pack(side="left", fill="x", expand=True, padx=10)
        
        # Actions
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        ctk.CTkButton(action_frame, text="Edit", width=35, height=35, 
                     fg_color="#E0F2FE", hover_color="#BAE6FD",
                     text_color="#0284C7", corner_radius=8,
                     command=lambda u=user: self.edit_user(u)).pack(side="left", padx=3)
        
        ctk.CTkButton(action_frame, text="Delete", width=35, height=35,
                     fg_color="#FEE2E2", hover_color="#FECACA",
                     text_color="#DC2626", corner_radius=8,
                     command=lambda u=user: self.delete_user(u)).pack(side="left", padx=3)

    def edit_user(self, user):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit User: {user['mssv']}")
        dialog.geometry("480x650")
        dialog.transient(self)
        dialog.configure(fg_color="white")
        dialog.resizable(False, False)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="#6366F1", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="Edit User", font=(self.FONT, 20, "bold"), 
                    text_color="white").pack(pady=25)
        
        # Form
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=30)
        
        # MSSV (readonly)
        ctk.CTkLabel(form, text="Student ID (MSSV)", font=(self.FONT, 12, "bold"), 
                    text_color="#64748B").pack(anchor="w", pady=(0, 5))
        mssv_display = ctk.CTkEntry(form, height=45, font=(self.FONT, 13),
                                   fg_color="#F1F5F9", border_color="#E2E8F0", state="disabled")
        mssv_display.insert(0, user['mssv'])
        mssv_display.pack(fill="x", pady=(0, 15))
        
        # Full Name
        ctk.CTkLabel(form, text="Full Name", font=(self.FONT, 12, "bold"), 
                    text_color="#1E293B").pack(anchor="w", pady=(0, 5))
        entry_name = ctk.CTkEntry(form, height=45, font=(self.FONT, 13),
                                 border_color="#E2E8F0", fg_color="#F8FAFC")
        entry_name.insert(0, user.get('full_name', ''))
        entry_name.pack(fill="x", pady=(0, 15))
        
        # Email
        ctk.CTkLabel(form, text="Email Address", font=(self.FONT, 12, "bold"), 
                    text_color="#1E293B").pack(anchor="w", pady=(0, 5))
        entry_email = ctk.CTkEntry(form, height=45, font=(self.FONT, 13),
                                  border_color="#E2E8F0", fg_color="#F8FAFC")
        entry_email.insert(0, user['email'])
        entry_email.pack(fill="x", pady=(0, 15))
        
        # Role
        ctk.CTkLabel(form, text="Role", font=(self.FONT, 12, "bold"), 
                    text_color="#1E293B").pack(anchor="w", pady=(0, 5))
        role_var = ctk.StringVar(value=user['role'])
        cb_role = ctk.CTkComboBox(form, values=["STUDENT", "CVHT", "ADMIN"], 
                                 height=45, variable=role_var,
                                 border_color="#E2E8F0", fg_color="#F8FAFC")
        cb_role.pack(fill="x", pady=(0, 15))
        
        # Active Status
        active_var = ctk.BooleanVar(value=user.get('is_active', True))
        status_frame = ctk.CTkFrame(form, fg_color="#F8FAFC", corner_radius=10)
        status_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkCheckBox(status_frame, text="Account is active", variable=active_var, 
                       font=(self.FONT, 13), fg_color="#10B981", hover_color="#059669").pack(padx=15, pady=15)
        
        def submit():
            data = {
                "full_name": entry_name.get().strip(),
                "email": entry_email.get().strip(),
                "role": role_var.get(),
                "is_active": active_var.get()
            }
            
            if not data["full_name"] or not data["email"]:
                messagebox.showwarning("Missing Data", "Please fill in all required fields")
                return
            
            success, msg = api.update_user(user['_id'], data)
            if success:
                messagebox.showinfo("Success", "User updated successfully!")
                dialog.destroy()
                self.refresh(None)
            else:
                messagebox.showerror("Error", f"Failed to update user:\n{msg}")
        
        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="Cancel", height=45,
                     fg_color="#F1F5F9", hover_color="#E2E8F0",
                     text_color="#64748B", corner_radius=10,
                     command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Save Changes", height=45,
                     fg_color="#6366F1", hover_color="#4F46E5",
                     corner_radius=10, font=(self.FONT, 14, "bold"),
                     command=submit).pack(side="right", fill="x", expand=True)

    def delete_user(self, user):
        confirm_msg = f"Are you sure you want to delete this user?\n\n"
        confirm_msg += f"MSSV: {user['mssv']}\n"
        confirm_msg += f"Name: {user.get('full_name', 'N/A')}\n\n"
        confirm_msg += "This action cannot be undone!"
        
        if messagebox.askyesno("Confirm Deletion", confirm_msg):
            success, msg = api.delete_user(user['_id'])
            if success:
                messagebox.showinfo("Success", "User deleted successfully")
                self.refresh(None)
            else:
                messagebox.showerror("Error", f"Failed to delete user:\n{msg}")
