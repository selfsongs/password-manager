# src/update/downloader.py
# 更新下载模块

import os
import hashlib
import requests
from src.config import UPDATE_DOWNLOAD_DIR


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
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

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
        if not os.path.exists(self.save_path):
            return False

        try:
            actual_md5 = self.calculate_md5(self.save_path)
            return actual_md5 == expected_md5
        except Exception:
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
