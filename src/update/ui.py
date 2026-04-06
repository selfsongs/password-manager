# src/update/ui.py
# 更新 UI 模块

import customtkinter as ctk
from src.config import VERSION


class UpdateDialog(ctk.CTkToplevel):
    """
    更新提示对话框
    """

    def __init__(self, parent, update_info, on_update, on_remind_later, on_ignore):
        super().__init__(parent)
        self.title("更新提示")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态窗口

        # 存储回调函数
        self.on_update = on_update
        self.on_remind_later = on_remind_later
        self.on_ignore = on_ignore

        # 创建 UI
        self.create_ui(update_info)

    def create_ui(self, update_info):
        """
        创建 UI
        """
        # 标题
        title_label = ctk.CTkLabel(
            self, text="发现新版本", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)

        # 版本信息
        version_frame = ctk.CTkFrame(self)
        version_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(version_frame, text="当前版本:",
                     anchor="w").pack(fill="x", pady=5)
        ctk.CTkLabel(version_frame, text=VERSION, font=(
            "Arial", 12, "bold"), anchor="w").pack(fill="x", pady=5)

        ctk.CTkLabel(version_frame, text="最新版本:",
                     anchor="w").pack(fill="x", pady=5)
        ctk.CTkLabel(version_frame, text=update_info.get('latest_version', '未知'), font=(
            "Arial", 12, "bold"), anchor="w").pack(fill="x", pady=5)

        # 更新内容
        changelog_frame = ctk.CTkFrame(self)
        changelog_frame.pack(pady=10, padx=20, fill="x", expand=True)

        ctk.CTkLabel(changelog_frame, text="更新内容:",
                     anchor="w").pack(fill="x", pady=5)

        changelog_text = ctk.CTkTextbox(changelog_frame, height=100)
        changelog_text.pack(fill="both", expand=True, pady=5)

        # 填充更新内容
        changelog = update_info.get('changelog', [])
        if changelog:
            for item in changelog:
                changelog_text.insert("end", f"• {item}\n")
        else:
            changelog_text.insert("end", "• 无详细更新内容")

        changelog_text.configure(state="disabled")  # 禁用编辑

        # 按钮
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20, padx=20, fill="x")

        ignore_button = ctk.CTkButton(
            button_frame, text="忽略此版本", command=self.on_ignore)
        ignore_button.pack(side="left", padx=10)

        remind_later_button = ctk.CTkButton(
            button_frame, text="稍后提醒", command=self.on_remind_later)
        remind_later_button.pack(side="left", padx=10)

        update_button = ctk.CTkButton(
            button_frame, text="立即更新", command=self.on_update, fg_color="#3B8ED0", hover_color="#2D70B3")
        update_button.pack(side="right", padx=10)


class DownloadProgressDialog(ctk.CTkToplevel):
    """
    下载进度对话框
    """

    def __init__(self, parent, on_cancel):
        super().__init__(parent)
        self.title("下载更新")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 存储回调函数
        self.on_cancel = on_cancel

        # 创建 UI
        self.create_ui()

    def create_ui(self):
        """
        创建 UI
        """
        # 标题
        title_label = ctk.CTkLabel(self, text="正在下载更新...", font=("Arial", 16))
        title_label.pack(pady=20)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        # 进度信息
        self.progress_label = ctk.CTkLabel(self, text="0%", font=("Arial", 12))
        self.progress_label.pack(pady=10)

        # 取消按钮
        cancel_button = ctk.CTkButton(
            self, text="取消下载", command=self.on_cancel)
        cancel_button.pack(pady=20)

    def update_progress(self, progress, total_size):
        """
        更新进度
        """
        self.progress_bar.set(progress / 100)
        self.progress_label.configure(
            text=f"{progress}% ({total_size / 1024 / 1024:.2f} MB)")
        self.update()  # 刷新界面


class UpdateUI:
    """
    更新 UI 类，管理更新相关的界面
    """

    def __init__(self, parent):
        self.parent = parent
        self.update_dialog = None
        self.download_dialog = None

    def show_update_dialog(self, update_info, on_update, on_remind_later, on_ignore):
        """
        显示更新提示对话框
        """
        self.update_dialog = UpdateDialog(
            self.parent,
            update_info,
            on_update,
            on_remind_later,
            on_ignore
        )
        return self.update_dialog

    def show_download_progress(self, on_cancel):
        """
        显示下载进度对话框
        """
        self.download_dialog = DownloadProgressDialog(self.parent, on_cancel)
        return self.download_dialog

    def show_message(self, title, message):
        """
        显示消息对话框
        """
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(title)
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=message, wraplength=280).pack(pady=20)
        ctk.CTkButton(dialog, text="确定", command=dialog.destroy).pack(pady=20)

        return dialog
