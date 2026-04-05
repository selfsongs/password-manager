"""
main.py - 程序入口
"""

from main_view import MainView
from auth_view import AuthView
import database as db
import customtkinter as ctk
import sys
import os

# 确保 src 目录在模块搜索路径中
sys.path.insert(0, os.path.dirname(__file__))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("密码管理器")
        self.geometry("760x560")
        self.minsize(640, 480)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        db.init_db()
        self._show_auth()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _show_auth(self):
        self._clear()
        self.geometry("480x520")
        auth = AuthView(self, on_login_success=self._show_main)
        auth.pack(fill="both", expand=True)

    def _show_main(self, user, master_password: str):
        self._clear()
        self.geometry("820x600")
        main = MainView(self, user, master_password, on_logout=self._show_auth)
        main.pack(fill="both", expand=True)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
