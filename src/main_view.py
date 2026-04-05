"""
main_view.py - 登录后的主界面
功能：密码列表、搜索、添加、编辑、删除、密码生成器
"""

import secrets
import string
import customtkinter as ctk
from tkinter import messagebox
import database as db
import crypto


class PasswordDialog(ctk.CTkToplevel):
    """添加 / 编辑密码条目的弹窗"""

    def __init__(
        self, master, master_password: str, salt: str, entry=None, on_save=None
    ):
        super().__init__(master)
        self.master_password = master_password
        self.salt = salt
        self.entry = entry  # None = 添加模式，否则为编辑模式
        self.on_save = on_save

        self.title("编辑密码" if entry else "添加密码")
        self.geometry("420x520")
        self.resizable(False, False)
        self.grab_set()
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 24, "fill": "x"}

        ctk.CTkLabel(
            self,
            text="编辑密码条目" if self.entry else "新增密码条目",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 16))

        fields = [
            ("网站名称 *", "site_name", False, "例：GitHub"),
            ("网址 (可选)", "url", False, "例：https://github.com"),
            ("账号 / 邮箱 *", "account", False, ""),
            ("密码 *", "password", True, ""),
            ("备注 (可选)", "notes", False, ""),
        ]

        self.vars: dict[str, ctk.CTkEntry] = {}
        for label, key, is_pw, ph in fields:
            ctk.CTkLabel(self, text=label, anchor="w").pack(**pad, pady=(8, 0))
            if key == "password":
                row = ctk.CTkFrame(self, fg_color="transparent")
                row.pack(**pad, pady=(4, 0))
                entry_w = ctk.CTkEntry(
                    row, placeholder_text=ph, show="●", height=36)
                entry_w.pack(side="left", fill="x", expand=True)
                # 生成密码按钮
                ctk.CTkButton(
                    row,
                    text="生成",
                    width=56,
                    height=36,
                    command=lambda e=entry_w: self._generate_password(e),
                ).pack(side="left", padx=(6, 0))
                # 显示/隐藏按钮
                self._pw_visible = False
                self._pw_entry = entry_w
                ctk.CTkButton(
                    row,
                    text="👁",
                    width=36,
                    height=36,
                    command=self._toggle_pw_visibility,
                ).pack(side="left", padx=(4, 0))
            else:
                entry_w = ctk.CTkEntry(self, placeholder_text=ph, height=36)
                entry_w.pack(**pad, pady=(4, 0))
            self.vars[key] = entry_w

        # 如果是编辑模式，预填数据（解密）
        if self.entry:
            self.vars["site_name"].insert(0, self.entry["site_name"])
            self.vars["url"].insert(0, self.entry["url"] or "")
            self.vars["account"].insert(
                0,
                crypto.decrypt(self.entry["account"],
                               self.master_password, self.salt),
            )
            self.vars["password"].insert(
                0,
                crypto.decrypt(self.entry["password"],
                               self.master_password, self.salt),
            )
            self.vars["notes"].insert(0, self.entry["notes"] or "")

        # 保存按钮
        ctk.CTkButton(self, text="保存", height=40, command=self._save).pack(
            padx=24, pady=20, fill="x"
        )

    def _toggle_pw_visibility(self):
        self._pw_visible = not self._pw_visible
        self._pw_entry.configure(show="" if self._pw_visible else "●")

    def _generate_password(self, entry_widget: ctk.CTkEntry):
        """生成 16 位高强度随机密码（使用密码学安全随机数）"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        # 确保包含每种字符类型（使用 secrets 模块保证密码学安全）
        pwd = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_=+"),
        ]
        pwd += [secrets.choice(chars) for _ in range(12)]
        # secrets.SystemRandom 提供密码学安全的 shuffle
        secure_random = secrets.SystemRandom()
        secure_random.shuffle(pwd)
        result = "".join(pwd)
        entry_widget.delete(0, "end")
        entry_widget.insert(0, result)
        # 显示明文方便确认
        entry_widget.configure(show="")
        self._pw_visible = True

    def _save(self):
        site = self.vars["site_name"].get().strip()
        url = self.vars["url"].get().strip()
        account = self.vars["account"].get().strip()
        password = self.vars["password"].get()
        notes = self.vars["notes"].get().strip()

        if not site or not account or not password:
            messagebox.showwarning("提示", "网站名称、账号和密码为必填项", parent=self)
            return

        # 加密账号和密码后存储
        enc_account = crypto.encrypt(account, self.master_password, self.salt)
        enc_password = crypto.encrypt(
            password, self.master_password, self.salt)

        if self.on_save:
            self.on_save(site, url, enc_account, enc_password, notes)
        self.destroy()


class MainView(ctk.CTkFrame):
    """登录后的主界面"""

    def __init__(self, master, user, master_password: str, on_logout):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.master_password = master_password
        self.salt = user["salt"]
        self.on_logout = on_logout
        self._build_ui()
        self._load_entries()

    def _build_ui(self):
        # ── 顶部栏 ──
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            top, text="密码管理器", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="退出登录",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            command=self.on_logout,
        ).pack(side="right")

        ctk.CTkLabel(
            top,
            text=f"用户：{self.user['username']}",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=12)

        # ── 搜索 + 添加 ──
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=12)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_entries())
        search = ctk.CTkEntry(
            bar,
            placeholder_text="搜索网站名称、网址或账号...",
            textvariable=self.search_var,
            height=36,
        )
        search.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            bar, text="+ 添加", width=90, height=36, command=self._add_entry
        ).pack(side="left", padx=(10, 0))

        # ── 列表区域 ──
        self.scroll = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _load_entries(self):
        """从数据库加载并渲染密码条目，支持对加密字段的搜索"""
        for w in self.scroll.winfo_children():
            w.destroy()

        keyword = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        # 先获取当前用户的所有条目
        all_entries = db.get_passwords(self.user["id"])

        # 在应用层过滤：对明文字段直接匹配，对加密字段解密后匹配
        if keyword:
            keyword_lower = keyword.lower()
            entries = []
            for row in all_entries:
                # 明文字段匹配
                if keyword_lower in (row["site_name"] or "").lower():
                    entries.append(row)
                    continue
                if keyword_lower in (row["url"] or "").lower():
                    entries.append(row)
                    continue
                # 加密字段解密后匹配
                try:
                    acc = crypto.decrypt(
                        row["account"], self.master_password, self.salt)
                    if keyword_lower in acc.lower():
                        entries.append(row)
                        continue
                except Exception:
                    pass
        else:
            entries = all_entries

        if not entries:
            ctk.CTkLabel(
                self.scroll, text="暂无密码记录，点击「+ 添加」新增", text_color="gray"
            ).pack(pady=40)
            return

        for row in entries:
            self._render_entry_card(row)

    def _render_entry_card(self, row):
        card = ctk.CTkFrame(self.scroll, corner_radius=10)
        card.pack(fill="x", pady=5)

        # 左侧信息
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info,
            text=row["site_name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        if row["url"]:
            ctk.CTkLabel(
                info,
                text=row["url"],
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
            ).pack(fill="x")

        # 解密账号显示（密码不直接显示）
        try:
            acc = crypto.decrypt(
                row["account"], self.master_password, self.salt)
        except Exception:
            acc = "(解密失败)"
        ctk.CTkLabel(
            info,
            text=f"账号：{acc}",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
            anchor="w",
        ).pack(fill="x")

        # 右侧按钮
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            btns,
            text="复制密码",
            width=80,
            height=30,
            command=lambda r=row: self._copy_password(r),
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btns,
            text="编辑",
            width=80,
            height=30,
            fg_color="transparent",
            border_width=1,
            command=lambda r=row: self._edit_entry(r),
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btns,
            text="删除",
            width=80,
            height=30,
            fg_color="#c0392b",
            hover_color="#922b21",
            command=lambda r=row: self._delete_entry(r),
        ).pack()

    def _copy_password(self, row):
        try:
            pw = crypto.decrypt(
                row["password"], self.master_password, self.salt)
        except Exception:
            messagebox.showerror("错误", "密码解密失败")
            return
        self.clipboard_clear()
        self.clipboard_append(pw)
        messagebox.showinfo("已复制", f"「{row['site_name']}」的密码已复制到剪贴板")

    def _add_entry(self):
        def on_save(site, url, enc_account, enc_password, notes):
            db.add_password(
                self.user["id"], site, url, enc_account, enc_password, notes
            )
            self._load_entries()

        PasswordDialog(
            self.winfo_toplevel(), self.master_password, self.salt, on_save=on_save
        )

    def _edit_entry(self, row):
        def on_save(site, url, enc_account, enc_password, notes):
            db.update_password(row["id"], site, url,
                               enc_account, enc_password, notes)
            self._load_entries()

        PasswordDialog(
            self.winfo_toplevel(),
            self.master_password,
            self.salt,
            entry=row,
            on_save=on_save,
        )

    def _delete_entry(self, row):
        if messagebox.askyesno(
            "确认删除",
            f"确定要删除「{row['site_name']}」的密码记录吗？\n此操作不可恢复。",
        ):
            db.delete_password(row["id"])
            self._load_entries()
