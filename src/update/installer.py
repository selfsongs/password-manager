# src/update/installer.py
# 更新安装模块

import os
import subprocess
import sys


class UpdateInstaller:
    """
    更新安装类，用于安装更新包
    """

    def __init__(self):
        self.installing = False
        self.error = None

    def create_updater_script(self, update_path, main_exe_path):
        """
        创建更新脚本
        update_path: 更新包路径
        main_exe_path: 主可执行文件路径
        """
        # 获取主可执行文件的目录
        main_exe_dir = os.path.dirname(main_exe_path)

        # 创建更新脚本路径
        script_path = os.path.join(main_exe_dir, "updater.bat")

        # 构建更新脚本内容
        if update_path.endswith('.zip'):
            # 处理 ZIP 压缩包
            script_content = f"""
@echo off

REM 等待主程序退出
timeout /t 2 > nul

REM 删除旧文件
if exist "{main_exe_dir}\\password_manager" (
    rd /s /q "{main_exe_dir}\\password_manager"
)

REM 解压更新包
powershell -Command "Expand-Archive -Path '{update_path}' -DestinationPath '{main_exe_dir}' -Force"

REM 启动主程序
start "" "{main_exe_path}"

REM 清理更新脚本
del /f /q "%~f0"

REM 清理更新目录
rd /s /q "%~dp0update"
"""
        else:
            # 处理单个可执行文件
            script_content = f"""
@echo off

REM 等待主程序退出
timeout /t 2 > nul

REM 复制更新文件
xcopy /y "{update_path}" "{main_exe_dir}"

REM 启动主程序
start "" "{main_exe_path}"

REM 清理更新脚本
del /f /q "%~f0"

REM 清理更新目录
rd /s /q "%~dp0update"
"""

        # 写入更新脚本
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return script_path

    def install_update(self, update_path):
        """
        安装更新包
        update_path: 更新包路径
        """
        self.installing = True
        self.error = None

        try:
            # 获取主可执行文件路径
            main_exe_path = sys.executable

            # 创建更新脚本
            script_path = self.create_updater_script(
                update_path, main_exe_path)

            # 启动更新脚本
            subprocess.Popen([script_path], shell=True)

            # 退出主程序
            sys.exit(0)

        except Exception as e:
            self.error = f"Install error: {str(e)}"
            self.installing = False
            return False

        return True

    def get_install_info(self):
        """
        获取安装信息
        """
        return {
            'installing': self.installing,
            'error': self.error
        }
