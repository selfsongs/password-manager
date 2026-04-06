# src/update/downloader.py
# 更新下载模块

import os
import hashlib
import requests
from config import UPDATE_DOWNLOAD_DIR


class UpdateDownloader:
    """
    更新下载类，用于下载更新包
    """

    def __init__(self):
        self.download_url = None
        self.save_path = None
        self.progress = 0
        self.total_size = 0
        self.downloading = False
        self.error = None

    def calculate_md5(self, file_path):
        """
        计算文件的 MD5 哈希值
        """
        # 转换为绝对路径
        absolute_path = os.path.abspath(file_path)
        print(f"[DEBUG] 计算 MD5 的文件路径: {file_path}")
        print(f"[DEBUG] 绝对路径: {absolute_path}")
        print(
            f"[DEBUG] 文件大小: {os.path.getsize(absolute_path) if os.path.exists(absolute_path) else '文件不存在'}")
        md5_hash = hashlib.md5()
        with open(absolute_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        result = md5_hash.hexdigest()
        print(f"[DEBUG] 计算结果: {result}")
        return result

    def download_update(self, download_url, callback=None):
        """
        下载更新包
        download_url: 下载链接
        callback: 回调函数，参数为 (progress, total_size, error)
        """
        self.download_url = download_url
        self.progress = 0
        self.total_size = 0
        self.downloading = True
        self.error = None

        # 创建下载目录
        if not os.path.exists(UPDATE_DOWNLOAD_DIR):
            os.makedirs(UPDATE_DOWNLOAD_DIR)

        # 生成保存路径
        filename = os.path.basename(download_url)
        self.save_path = os.path.join(UPDATE_DOWNLOAD_DIR, filename)
        # 转换为绝对路径
        self.save_path = os.path.abspath(self.save_path)
        print(f"[DEBUG] 下载保存路径: {self.save_path}")
        print(
            f"[DEBUG] 目录是否存在: {os.path.exists(os.path.dirname(self.save_path))}")
        # 确保目录存在
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))
            print(f"[DEBUG] 目录已创建: {os.path.dirname(self.save_path)}")

        try:
            # 发送请求
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # 获取文件大小
            self.total_size = int(response.headers.get('content-length', 0))

            # 写入文件
            downloaded_size = 0
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self.progress = int(
                            (downloaded_size / self.total_size) * 100) if self.total_size > 0 else 0
                        if callback and self.progress < 100:
                            callback(self.progress, self.total_size, None)

            # 文件句柄已关闭，通知下载完成
            self.progress = 100
            if callback:
                callback(self.progress, self.total_size, None)

        except requests.RequestException as e:
            self.error = f"Download error: {str(e)}"
            if callback:
                callback(self.progress, self.total_size, self.error)
        finally:
            self.downloading = False

        return self.save_path

    def verify_download(self, expected_md5):
        """
        验证下载文件的完整性
        expected_md5: 期望的 MD5 哈希值
        """
        # 打印当前工作目录
        print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
        # 打印保存路径
        print(f"[DEBUG] 保存路径: {self.save_path}")
        # 打印绝对路径
        absolute_path = os.path.abspath(self.save_path)
        print(f"[DEBUG] 绝对路径: {absolute_path}")
        # 检查文件是否存在
        print(f"[DEBUG] 文件是否存在: {os.path.exists(absolute_path)}")
        # 检查文件大小
        if os.path.exists(absolute_path):
            print(f"[DEBUG] 文件大小: {os.path.getsize(absolute_path)}")
        else:
            print(f"[ERROR] 文件不存在: {absolute_path}")
            return False

        try:
            # 计算 MD5
            actual_md5 = self.calculate_md5(absolute_path)
            print(f"[DEBUG] 实际 MD5: {actual_md5}")
            print(f"[DEBUG] 期望 MD5: {expected_md5}")
            # 统一大小写进行比较
            return actual_md5.lower() == expected_md5.lower()
        except Exception as e:
            print(f"[ERROR] 计算 MD5 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_download_info(self):
        """
        获取下载信息
        """
        return {
            'download_url': self.download_url,
            'save_path': self.save_path,
            'progress': self.progress,
            'total_size': self.total_size,
            'downloading': self.downloading,
            'error': self.error
        }