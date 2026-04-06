# src/update/checker.py
# 更新检查模块

import json
import requests
import threading
from config import VERSION, UPDATE_CHECK_URL, UPDATE_CHECK_TIMEOUT


class UpdateChecker:
    """
    更新检查类，用于检查是否有新版本
    """

    def __init__(self):
        self.local_version = VERSION
        self.remote_version = None
        self.update_available = False
        self.update_info = {}
        self.checking = False
        self.error = None

    def compare_versions(self, version1, version2):
        """
        比较两个版本号
        返回 1（version1 > version2）、0（相等）或 -1（version1 < version2）
        """
        try:
            # 处理版本号，确保每个部分都是有效的整数
            def parse_version(version):
                parts = version.split('.')
                # 过滤空字符串并转换为整数
                return [int(part) for part in parts if part.strip()]

            v1_parts = parse_version(version1)
            v2_parts = parse_version(version2)

            for i in range(max(len(v1_parts), len(v2_parts))):
                v1 = v1_parts[i] if i < len(v1_parts) else 0
                v2 = v2_parts[i] if i < len(v2_parts) else 0

                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1

            return 0
        except (ValueError, AttributeError):
            # 如果版本号格式不正确，默认认为没有更新
            return -1

    def check_for_updates(self, callback=None):
        """
        检查是否有更新
        callback: 回调函数，参数为 (update_available, update_info, error)
        """
        def _check():
            self.checking = True
            self.error = None

            try:
                # 发送请求获取远程版本信息
                response = requests.get(
                    UPDATE_CHECK_URL, timeout=UPDATE_CHECK_TIMEOUT)
                response.raise_for_status()

                # 解析版本信息
                self.update_info = response.json()
                self.remote_version = self.update_info.get('latest_version')

                # 比较版本
                if self.remote_version:
                    comparison = self.compare_versions(
                        self.remote_version, self.local_version)
                    self.update_available = comparison > 0
                    # 输出版本信息
                    print(
                        f"当前版本: {self.local_version}, 最新版本: {self.remote_version}")
                else:
                    self.error = "Invalid version information"

            except requests.RequestException as e:
                self.error = f"Network error: {str(e)}"
            except json.JSONDecodeError:
                self.error = "Invalid JSON response"
            finally:
                self.checking = False
                if callback:
                    callback(self.update_available,
                             self.update_info, self.error)

        # 在后台线程中执行检查
        thread = threading.Thread(target=_check)
        thread.daemon = True
        thread.start()
        return thread

    def get_update_info(self):
        """
        获取更新信息
        """
        return {
            'local_version': self.local_version,
            'remote_version': self.remote_version,
            'update_available': self.update_available,
            'update_info': self.update_info,
            'error': self.error
        }
