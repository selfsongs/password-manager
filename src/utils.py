# src/utils.py
# 公共工具模块

import webbrowser
import customtkinter as ctk


def show_github_dialog(parent):
    """
    显示 GitHub 仓库链接对话框
    """
    github_url = "https://github.com/selfsongs/password-manager"

    # 创建一个新的对话框
    dialog = ctk.CTkToplevel(parent)
    dialog.title("GitHub仓库")
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # 显示仓库地址
    ctk.CTkLabel(dialog, text="GitHub 仓库地址:", font=ctk.CTkFont(
        size=14, weight="bold")).pack(pady=(20, 10))
    ctk.CTkLabel(dialog, text=github_url, wraplength=380).pack(pady=(0, 20))

    # 按钮框架
    button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    button_frame.pack(pady=10, padx=20, fill="x")

    # 取消按钮
    ctk.CTkButton(
        button_frame, text="取消", width=100, command=dialog.destroy
    ).pack(side="left", padx=10)

    # 前往按钮
    ctk.CTkButton(
        button_frame, text="前往仓库", width=100,
        command=lambda: (webbrowser.open(github_url), dialog.destroy())
    ).pack(side="right", padx=10)
