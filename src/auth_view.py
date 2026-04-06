"""
auth_view.py - 登录 / 注册界面
使用两个独立 Frame 分别承载登录和注册表单，切换时整体替换，避免动态 pack/pack_forget 的布局问题。
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
import crypto
from utils import show_github_dialog


class AuthView(ctk.CTkFrame):
    """
    登录/注册界面，登录成功后调用 on_login_success(user_row, master_password)
    """

    def __init__(self, master, on_login_success, on_check_update=None):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.on_check_update = on_check_update
        self._build_ui()

    def _build_ui(self):
        # 顶部栏 - 包含检查更新按钮
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 0))

        # 检查更新按钮
        if self.on_check_update:
            ctk.CTkButton(
                top_bar,
                text="检查更新",
                width=90,
                height=32,
                fg_color="transparent",
                border_width=1,
                command=self.on_check_update,
            ).pack(side="right", padx=(0, 10))

        # GitHub仓库按钮
        ctk.CTkButton(
            top_bar,
            text="GitHub仓库地址",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            command=self._show_github,
        ).pack(side="right")

        # 标题区
        ctk.CTkLabel(
            self, text="密码管理器", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(40, 6))
        ctk.CTkLabel(
            self,
            text="安全保管您的所有密码",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(pady=(0, 24))

        # Tab 切换按钮（在卡片外面，避免影响卡片高度）
        self.tab = ctk.CTkSegmentedButton(
            self, values=["登录", "注册"], command=self._on_tab_change, width=300
        )
        self.tab.set("登录")
        self.tab.pack(pady=(0, 16))

        # 表单容器（卡片），不锁定高度，让内容自适应
        self.card = ctk.CTkFrame(self, corner_radius=16, width=360)
        self.card.pack(padx=40, pady=0)

        # 构建两套表单
        self._login_frame = self._build_login_form(self.card)
        self._register_frame = self._build_register_form(self.card)

        # 默认显示登录
        self._show_login()

    # ── 登录表单 ──────────────────────────────────────────
    def _build_login_form(self, parent) -> ctk.CTkFrame:
        f = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(f, text="用户名", anchor="w").pack(padx=30, fill="x")
        self.login_username = ctk.CTkEntry(
            f, placeholder_text="请输入用户名", height=38
        )
        self.login_username.pack(padx=30, pady=(4, 14), fill="x")

        ctk.CTkLabel(f, text="主密码", anchor="w").pack(padx=30, fill="x")
        self.login_password = ctk.CTkEntry(
            f, placeholder_text="请输入主密码", show="●", height=38
        )
        self.login_password.pack(padx=30, pady=(4, 14), fill="x")

        btn = ctk.CTkButton(f, text="登录", height=40, command=self._do_login)
        btn.pack(padx=30, pady=(4, 24), fill="x")

        self.login_password.bind("<Return>", lambda e: self._do_login())
        return f

    # ── 注册表单 ──────────────────────────────────────────
    def _build_register_form(self, parent) -> ctk.CTkFrame:
        f = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(f, text="用户名", anchor="w").pack(padx=30, fill="x")
        self.reg_username = ctk.CTkEntry(
            f, placeholder_text="请输入用户名", height=38)
        self.reg_username.pack(padx=30, pady=(4, 14), fill="x")

        ctk.CTkLabel(f, text="主密码", anchor="w").pack(padx=30, fill="x")
        self.reg_password = ctk.CTkEntry(
            f, placeholder_text="请输入主密码（至少6位）", show="●", height=38
        )
        self.reg_password.pack(padx=30, pady=(4, 14), fill="x")

        ctk.CTkLabel(f, text="确认主密码", anchor="w").pack(padx=30, fill="x")
        self.reg_confirm = ctk.CTkEntry(
            f, placeholder_text="再次输入主密码", show="●", height=38
        )
        self.reg_confirm.pack(padx=30, pady=(4, 10), fill="x")

        ctk.CTkLabel(
            f,
            text="注意：主密码忘记后无法找回，请牢记！",
            font=ctk.CTkFont(size=11),
            text_color="orange",
        ).pack(padx=30, pady=(0, 10))

        btn = ctk.CTkButton(f, text="注册", height=40, command=self._do_register)
        btn.pack(padx=30, pady=(4, 24), fill="x")

        self.reg_confirm.bind("<Return>", lambda e: self._do_register())
        return f

    # ── Tab 切换 ──────────────────────────────────────────
    def _on_tab_change(self, value: str):
        if value == "登录":
            self._show_login()
        else:
            self._show_register()

    def _show_login(self):
        self._register_frame.pack_forget()
        self._login_frame.pack(fill="x", pady=(16, 0))
        self.login_username.focus()

    def _show_register(self):
        self._login_frame.pack_forget()
        self._register_frame.pack(fill="x", pady=(16, 0))
        self.reg_username.focus()

    # ── 登录逻辑 ──────────────────────────────────────────
    def _do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()
        if not username or not password:
            messagebox.showwarning("提示", "用户名和密码不能为空")
            return
        user = db.get_user(username)
        if not user:
            messagebox.showerror("登录失败", "用户名不存在")
            return
        if not crypto.verify_password(password, user["password_hash"]):
            messagebox.showerror("登录失败", "密码错误")
            return
        self.on_login_success(user, password)

    # ── 注册逻辑 ──────────────────────────────────────────
    def _do_register(self):
        username = self.reg_username.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()

        if not username or not password:
            messagebox.showwarning("提示", "用户名和密码不能为空")
            return
        if len(password) < 6:
            messagebox.showwarning("提示", "主密码长度至少 6 位")
            return
        if password != confirm:
            messagebox.showerror("注册失败", "两次输入的密码不一致")
            return
        if db.username_exists(username):
            messagebox.showerror("注册失败", "用户名已存在")
            return

        salt = crypto.generate_salt()
        pw_hash = crypto.hash_password(password)
        db.create_user(username, pw_hash, salt)
        messagebox.showinfo("注册成功", f"用户 '{username}' 注册成功，请登录")

        # 切回登录并清空注册表单
        self.tab.set("登录")
        self._show_login()
        self.reg_username.delete(0, "end")
        self.reg_password.delete(0, "end")
        self.reg_confirm.delete(0, "end")

    def _show_github(self):
        """显示GitHub仓库链接"""
        show_github_dialog(self.winfo_toplevel())
