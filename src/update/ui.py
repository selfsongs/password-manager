# src/update/ui.py
# 更新 UI 模块

import customtkinter as ctk
from config import VERSION


class UpdateDialog(ctk.CTkToplevel):
    """
    更新提示对话框
    """

    def __init__(self, parent, update_info, on_update, on_remind_later, on_ignore):
        super().__init__(parent)
        self.title("更新提示")
        self.geometry("500x400")  # 初始大小
        self.resizable(True, True)  # 允许窗口拖拽缩放
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态窗口

        # 存储回调函数
        self.on_update = on_update
        self.on_remind_later = on_remind_later
        self.on_ignore = on_ignore

        # 创建 UI
        self.create_ui(update_info)

        # 自动调整窗口大小以适应内容
        self.update_idletasks()
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}")

    def create_ui(self, update_info):
        """
        创建 UI
        """
        # 使用网格布局，更灵活
        self.grid_rowconfigure(0, weight=0)  # 标题
        self.grid_rowconfigure(1, weight=0)  # 版本信息
        self.grid_rowconfigure(2, weight=1)  # 更新内容（可伸缩）
        self.grid_rowconfigure(3, weight=0)  # 按钮
        self.grid_columnconfigure(0, weight=1)  # 列可伸缩

        # 标题
        title_label = ctk.CTkLabel(
            self, text="发现新版本", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, pady=20, padx=20, sticky="n")

        # 版本信息
        version_frame = ctk.CTkFrame(self)
        version_frame.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        version_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(version_frame, text="当前版本:",
                     anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        ctk.CTkLabel(version_frame, text=VERSION, font=(
            "Arial", 12, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=5)

        ctk.CTkLabel(version_frame, text="最新版本:",
                     anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        ctk.CTkLabel(version_frame, text=update_info.get('latest_version', '未知'), font=(
            "Arial", 12, "bold"), anchor="w").grid(row=3, column=0, sticky="w", pady=5)

        # 更新内容
        changelog_frame = ctk.CTkFrame(self)
        changelog_frame.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")
        changelog_frame.grid_rowconfigure(1, weight=1)
        changelog_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(changelog_frame, text="更新内容:",
                     anchor="w").grid(row=0, column=0, sticky="w", pady=5)

        changelog_text = ctk.CTkTextbox(changelog_frame)
        changelog_text.grid(row=1, column=0, sticky="nsew", pady=5)

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
        button_frame.grid(row=3, column=0, pady=20, padx=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        ignore_button = ctk.CTkButton(
            button_frame, text="忽略此版本", command=self.on_ignore)
        ignore_button.grid(row=0, column=0, padx=10, sticky="w")

        remind_later_button = ctk.CTkButton(
            button_frame, text="稍后提醒", command=self.on_remind_later)
        remind_later_button.grid(row=0, column=1, padx=10, sticky="n")

        update_button = ctk.CTkButton(
            button_frame, text="立即更新", command=self.on_update, fg_color="#3B8ED0", hover_color="#2D70B3")
        update_button.grid(row=0, column=2, padx=10, sticky="e")


class DownloadProgressDialog(ctk.CTkToplevel):
    """
    下载进度对话框
    """

    def __init__(self, parent, on_cancel):
        super().__init__(parent)
        self.title("下载更新")
        self.geometry("400x200")
        self.minsize(400, 200)  # 设置最小大小，确保所有内容都能完整显示
        self.resizable(True, True)  # 允许窗口拖拽缩放
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
        dialog.minsize(300, 200)  # 设置最小大小，确保所有内容都能完整显示
        dialog.resizable(True, True)  # 允许窗口拖拽缩放
        dialog.transient(self.parent)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=message, wraplength=280).pack(pady=20)
        ctk.CTkButton(dialog, text="确定", command=dialog.destroy).pack(pady=20)

        return dialog
