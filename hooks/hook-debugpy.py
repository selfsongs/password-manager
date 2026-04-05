# hook-debugpy.py
from PyInstaller.utils.hooks import collect_all

# 收集 debugpy 的所有依赖
datas, binaries, hiddenimports = collect_all('debugpy')

# 添加可能缺少的标准库依赖
hiddenimports.extend([
    'code',
    'codeop',
    'contextlib',
    'xmlrpc.server',
    'xmlrpc.client',
    'select',
    'threading',
    'queue',
    'socket',
    'os',
    'sys',
    'time',
    'traceback',
    'inspect',
    'importlib',
    'json',
    'pickle'
])

# 打印收集的依赖，用于调试
print(f"Collected hidden imports for debugpy: {hiddenimports}")
