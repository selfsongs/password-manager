"""
main.py - 程序入口
"""
import os
import sys
import argparse
import customtkinter as ctk
import database as db
from auth_view import AuthView
from main_view import MainView

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
        # 等待连接，确保调试器有足够时间连接
        debugpy.wait_for_client()
        print("VSCode 调试器已连接，开始执行程序...")

        # 在冻结环境中手动设置路径映射
        # debugpy 的 pathMappings 在冻结环境中可能不生效，需要通过 pydevd 内部 API 强制映射
        if getattr(sys, 'frozen', False):
            try:
                _internal_dir = getattr(
                    sys, '_MEIPASS', os.path.dirname(sys.executable))
                # 源码目录：从 _internal 往上推算到项目的 src 目录
                # _internal = .../dist/password_manager/_internal
                # src = .../src
                _dist_pm_dir = os.path.dirname(
                    _internal_dir)  # dist/password_manager
                _dist_dir = os.path.dirname(_dist_pm_dir)       # dist
                _project_dir = os.path.dirname(_dist_dir)        # project root
                _src_dir = os.path.join(_project_dir, 'src')

                if os.path.exists(_src_dir):
                    from debugpy._vendored.pydevd.pydevd_file_utils import setup_client_server_paths
                    setup_client_server_paths([(_src_dir, _internal_dir)])
                    print(f"路径映射已设置: {_src_dir} <-> {_internal_dir}")
                else:
                    print(f"[WARN] 源码目录不存在: {_src_dir}，断点可能无法命中")
                    print(f"[WARN] 请确保 exe 在 dist/password_manager/ 目录下运行")
            except Exception as e:
                print(f"[WARN] 设置路径映射失败: {e}")
    except Exception as e:
        print(f"启动远程调试服务失败: {e}")
        # 即使调试服务启动失败，也继续执行程序
        pass


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
