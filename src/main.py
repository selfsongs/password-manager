# fmt: off
"""
main.py - 程序入口
"""
import os
import sys

# 确保 src 目录在模块搜索路径中
sys.path.insert(0, os.path.dirname(__file__))

import argparse
import customtkinter as ctk
import database as db
from auth_view import AuthView
from main_view import MainView
from update.checker import UpdateChecker
from update.downloader import UpdateDownloader
from update.installer import UpdateInstaller
from update.ui import UpdateUI

# fmt: on

# 解析命令行参数
parser = argparse.ArgumentParser(description="密码管理器")
parser.add_argument('--debug', action='store_true', help='启用远程调试功能')
args = parser.parse_args()

# 如果启用了调试模式，启动远程调试服务
if args.debug:
    import socket

    # 设置必要的环境变量，解决冻结模块问题
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
    os.environ['PYDEVD_USE_CYTHON'] = 'NO'

    # 检查是否在冻结环境中运行
    if getattr(sys, 'frozen', False):
        print("在冻结环境中运行，启用调试模式...")
        # debugpy.configure(python=...) 需要指定一个 Python 解释器路径
        # 但配合 subProcess=False，debugpy adapter 以线程模式运行在主进程内，
        # 实际上不会启动外部子进程，因此不依赖目标机器安装 Python。
        # 这里仍然查找一个 python 路径作为配置项，优先用系统 PATH 中的，
        # 找不到则 fallback 到 sys.executable（exe 自身）。
        import shutil
        _sys_python = shutil.which('python')
        _python_exe = _sys_python if _sys_python else sys.executable
        os.environ['DEBUGPY_PYTHON'] = _python_exe
        print(f"调试用 Python 解释器: {_python_exe}")

    # 检查端口是否可用
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    port = 5678
    if not is_port_available(port):
        print(f"端口 {port} 已被占用，尝试使用其他端口...")
        port = 5679
        if not is_port_available(port):
            print(f"端口 {port} 也被占用，尝试使用其他端口...")
            port = 5680

    # 启动远程调试服务，监听端口
    print(f"尝试启动远程调试服务，监听端口 {port}...")
    try:
        # 延迟导入 debugpy，确保环境变量已设置
        import debugpy
        # 在冻结环境中配置 python 路径和子进程调试
        if getattr(sys, 'frozen', False):
            if os.environ.get('DEBUGPY_PYTHON'):
                debugpy.configure(python=os.environ['DEBUGPY_PYTHON'])
            # 关键：配置 subProcess=False，避免 debugpy 尝试在子进程中调试
            # 冻结环境中子进程调试会失败
            debugpy.configure(subProcess=False)
        # 启动远程调试服务
        debugpy.listen(('0.0.0.0', port))
        print("远程调试服务已启动，等待 VSCode 连接...")
        print(f"请在 VSCode 中使用端口 {port} 连接")
        print("注意：如果连接失败，请检查防火墙设置或尝试使用不同端口")
        print("")
        print("=== 调试路径映射信息 ===")
        if getattr(sys, 'frozen', False):
            _internal_dir = getattr(
                sys, '_MEIPASS', os.path.dirname(sys.executable))
            print(f"远程临时目录: {_internal_dir}")
            print("请在 VSCode launch.json 中设置 pathMappings:")
            print('"pathMappings": [')
            print('    {')
            print('        "localRoot": "${workspaceFolder}/src",')
            print(f'        "remoteRoot": "{_internal_dir}"')
            print('    }')
            print(']')
        else:
            print("当前在非冻结环境中运行")
            print('请在 VSCode launch.json 中设置 pathMappings:')
            print('"pathMappings": [')
            print('    {')
            print('        "localRoot": "${workspaceFolder}/src",')
            print('        "remoteRoot": "${workspaceFolder}/src"')
            print('    }')
            print(']')
        print("=====================")
        print("")
        # 等待连接，确保调试器有足够时间连接
        debugpy.wait_for_client()
        print("VSCode 调试器已连接，开始执行程序...")
    except Exception as e:
        print(f"启动远程调试服务失败: {e}")
        # 即使调试服务启动失败，也继续执行程序
        pass


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

        # 初始化更新相关组件
        self.update_ui = UpdateUI(self)
        self.update_checker = UpdateChecker()
        self.update_downloader = UpdateDownloader()
        self.update_installer = UpdateInstaller()

        # 自动检查更新，无更新时不显示弹窗
        self.check_for_updates(show_no_update_message=False)

        # 在界面右下角显示版本号
        from config import VERSION
        self.version_label = ctk.CTkLabel(
            self,
            text=f"版本: {VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.version_label.place(relx=0.98, rely=0.98, anchor="se")

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _show_auth(self):
        self._clear()
        self.geometry("480x520")
        auth = AuthView(self, on_login_success=self._show_main,
                        on_check_update=self.check_for_updates)
        auth.pack(fill="both", expand=True)

    def _show_main(self, user, master_password: str):
        self._clear()
        self.geometry("820x600")
        main = MainView(self, user, master_password, on_logout=self._show_auth,
                        on_check_update=self.check_for_updates)
        main.pack(fill="both", expand=True)

    def check_for_updates(self, show_no_update_message=True):
        """
        检查更新
        show_no_update_message: 是否在无更新时显示消息
        """
        def on_check_complete(update_available, update_info, error):
            if error:
                print(f"检查更新失败: {error}")
            elif update_available:
                # 显示更新提示对话框
                def on_update():
                    self.download_update(update_info)

                def on_remind_later():
                    print("稍后提醒")

                def on_ignore():
                    print("忽略此版本")

                self.update_ui.show_update_dialog(
                    update_info, on_update, on_remind_later, on_ignore)
            else:
                # 无更新
                from config import VERSION
                print(f"当前已是最新版本: {VERSION}")
                if show_no_update_message:
                    # 显示弹窗
                    self.update_ui.show_message("检查更新", f"当前已是最新版本: {VERSION}")

        # 开始检查更新
        self.update_checker.check_for_updates(on_check_complete)

    def download_update(self, update_info):
        """
        下载更新
        """
        download_url = update_info.get('download_url')
        expected_md5 = update_info.get('md5_hash')

        if not download_url:
            self.update_ui.show_message("错误", "下载链接无效")
            return

        # 显示下载进度对话框
        download_dialog = self.update_ui.show_download_progress(lambda: None)

        def on_download_progress(progress, total_size, error):
            if error:
                download_dialog.destroy()
                self.update_ui.show_message("错误", f"下载失败: {error}")
            else:
                download_dialog.update_progress(progress, total_size)
                if progress == 100:
                    # 下载完成，验证文件
                    if self.update_downloader.verify_download(expected_md5):
                        download_dialog.destroy()
                        # 安装更新
                        self.install_update(self.update_downloader.save_path)
                    else:
                        download_dialog.destroy()
                        self.update_ui.show_message("错误", "下载文件损坏，请重试。")

        # 开始下载
        self.update_downloader.download_update(
            download_url, on_download_progress)

    def install_update(self, update_path):
        """
        安装更新
        """
        # 显示安装提示
        self.update_ui.show_message("安装更新", "正在安装更新，请稍候...")

        # 安装更新
        self.update_installer.install_update(update_path)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
