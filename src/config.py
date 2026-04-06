# src/config.py
# 版本配置文件

VERSION = "1.0.0"
"""
版本号格式：主版本.次版本.修订号
- 主版本：不兼容的重大变更
- 次版本：添加新功能
- 修订号：修复 bug
"""

# 更新检查配置
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/selfsongs/password-manager/master/version.json"
"""
远程版本信息文件的 URL
"""

# 检查更新的超时时间（秒）
UPDATE_CHECK_TIMEOUT = 5

# 更新包下载目录
UPDATE_DOWNLOAD_DIR = "update"  # src/config.py
VERSION = "1.0.0"
