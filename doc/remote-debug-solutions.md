# Python 客户端远程调试技术方案

> 适用于 Python 打包（PyInstaller / cx_Freeze / Nuitka 等）后的桌面客户端，在不暴露源码的前提下进行远程问题诊断和调试。

---

## 方案概览

| 方案                        | 核心思路                 | 能否设断点 | 是否暴露源码 |   目标机器依赖   | 适用阶段  | 实现成本 |
| --------------------------- | ------------------------ | :--------: | :----------: | :--------------: | --------- | :------: |
| **① debugpy 远程调试**      | VSCode attach 到远程进程 |     ✅      | ⚠️ Debug 版会 |  无（线程模式）  | 开发/内测 |    ⭐⭐    |
| **② Sentry 异常追踪**       | 自动上报异常堆栈         |     ❌      |      ❌       |      需联网      | 内测/生产 |    ⭐     |
| **③ 结构化日志 + 远程收集** | 日志聚合分析             |     ❌      |      ❌       |    视方案而定    | 全阶段    |    ⭐⭐    |
| **④ 远程 REPL / RPC 诊断**  | 远程执行诊断命令         |     ❌      |      ❌       |        无        | 内测/生产 |   ⭐⭐⭐    |
| **⑤ 条件性源码映射**        | 开发者挂载源码到目标机   |     ✅      | ⚠️ 需网络共享 | Python + debugpy | 开发      |   ⭐⭐⭐    |
| **⑥ 核心转储 + 离线分析**   | 崩溃时生成 dump 文件     |     ❌      |      ❌       |        无        | 生产      |   ⭐⭐⭐⭐   |

---

## 方案一：debugpy 远程调试

### 原理

```
目标机器                              开发者机器
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe --debug      │            │ VSCode              │
│                      │            │   + Python 扩展      │
│ debugpy.listen(5678) │◄── DAP ────│   Attach to 5678    │
│ pydevd 调试引擎       │            │   源码 src/ 打断点   │
│                      │            │                     │
│ subProcess=False     │            │                     │
│ (线程模式 adapter)    │            │                     │
└──────────────────────┘            └─────────────────────┘
```

### 关键技术点

- **debugpy** 是 VSCode 官方的 Python 调试协议（DAP）实现
- `debugpy.listen()` 启动 DAP 服务端，`debugpy.wait_for_client()` 等待 IDE 连接
- 冻结环境下需要 `subProcess=False` 让 adapter 以线程模式运行，避免启动子进程
- 需要通过 `setup_client_server_paths` 手动注册源码路径映射（`launch.json` 的 `pathMappings` 在冻结环境中可能不生效）
- 需要 `--add-data` 将 `.py` 源码文件打入包中，debugpy 需要读取源文件才能设置断点

### 冻结环境适配清单

| 问题                   | 解决方案                               |
| ---------------------- | -------------------------------------- |
| 字节码校验失败         | `PYDEVD_DISABLE_FILE_VALIDATION=1`     |
| Cython 加速模块不兼容  | `PYDEVD_USE_CYTHON=NO`                 |
| adapter 子进程启动失败 | `debugpy.configure(subProcess=False)`  |
| 断点路径不匹配         | `setup_client_server_paths()` 手动映射 |
| 磁盘上无 .py 源文件    | PyInstaller `--add-data "src/*.py;."`  |

### 优点

- 完整的交互式调试体验（断点、单步、变量查看、调用栈）
- VSCode 原生支持，开发者零学习成本
- 被调试端零依赖（`subProcess=False` 线程模式下）

### 缺点

- Debug 版需要将 `.py` 源码打入包中，有泄露风险
- 只适合开发/内测阶段，不适合生产环境
- 需要网络直连（端口可达）

### 示例代码

```python
import debugpy
import os, sys

os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
os.environ['PYDEVD_USE_CYTHON'] = 'NO'

debugpy.configure(subProcess=False)
debugpy.listen(('0.0.0.0', 5678))
debugpy.wait_for_client()

# 路径映射（冻结环境）
if getattr(sys, 'frozen', False):
    from debugpy._vendored.pydevd.pydevd_file_utils import setup_client_server_paths
    setup_client_server_paths([('/path/to/src', '/path/to/_internal')])
```

---

## 方案二：Sentry 异常追踪

### 原理

```
目标机器                              Sentry 云服务
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe              │            │ Sentry Dashboard    │
│                      │            │                     │
│ try:                 │  HTTPS     │ 异常列表            │
│   business_logic()   │──────────►│ 堆栈追踪            │
│ except:              │            │ 环境信息            │
│   sentry_sdk.capture │            │ 用户反馈            │
│                      │            │ 性能监控            │
└──────────────────────┘            └─────────────────────┘
                                           │
                                           ▼
                                    开发者浏览器查看
```

### 关键技术点

- **Sentry** 是业界最成熟的错误追踪平台，Python SDK 一行代码即可集成
- 自动捕获未处理异常，上报完整堆栈、局部变量、OS/Python 版本等上下文
- 支持 Source Maps 概念——上传源码映射后，即使客户端无源码也能在 Dashboard 中看到源码级堆栈
- 支持自定义 tag、breadcrumb（面包屑，记录异常前的操作路径）
- 免费版支持 5K events/月，足够小型项目使用

### 优点

- **不暴露源码**——客户端只上报堆栈信息，源码在 Sentry 服务端关联
- 生产环境可用，不影响性能
- 自动聚合相同异常，提供趋势分析
- 支持邮件/Slack/钉钉告警

### 缺点

- 只能看到异常发生时的堆栈快照，无法交互式调试
- 需要网络连接才能上报
- 非崩溃类 bug（如逻辑错误、UI 异常）需要手动埋点

### 示例代码

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-key@sentry.io/project-id",
    traces_sample_rate=0.1,  # 10% 性能监控采样
    environment="production",
    release="password-manager@1.0.0",
)

# 自动捕获异常，也可手动上报
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    sentry_sdk.set_context("user_action", {"last_click": "save_password"})
```

### PyInstaller 打包注意

```bash
# Sentry 需要 certifi（SSL 证书），PyInstaller 可能不会自动打包
pip install sentry-sdk certifi
pyinstaller --hidden-import=sentry_sdk.integrations --collect-data certifi ...
```

---

## 方案三：结构化日志 + 远程收集

### 原理

```
目标机器                              日志服务器
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe              │            │ ELK / Loki / 自建   │
│                      │            │                     │
│ logger.info(...)     │  上传/推送  │ 日志查询            │
│ logger.error(...)    │──────────►│ 关键字搜索          │
│                      │            │ 时间线分析          │
│ → app.log (本地)     │            │ 告警规则            │
│ → remote handler     │            │                     │
└──────────────────────┘            └─────────────────────┘
```

### 三种收集方式

#### 方式 A：本地日志 + 手动收集（最简单）

```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("用户点击了保存按钮", extra={"user_id": 123})
```

用户遇到问题时手动发送 `app.log` 文件给开发者。

#### 方式 B：HTTP 远程日志（中等复杂度）

```python
import logging
from logging.handlers import HTTPHandler

# 将日志通过 HTTP POST 发送到服务器
http_handler = HTTPHandler(
    host='logs.yourserver.com',
    url='/api/logs',
    method='POST',
    secure=True,
)
http_handler.setLevel(logging.ERROR)  # 只上报 ERROR 及以上
logging.getLogger().addHandler(http_handler)
```

#### 方式 C：ELK / Grafana Loki（企业级）

```
客户端 → Filebeat/Promtail → Elasticsearch/Loki → Kibana/Grafana
```

### 优点

- 完全不暴露源码
- 可以在生产环境长期运行
- 支持事后分析（"昨天下午 3 点用户遇到的问题"）
- 结合结构化日志（JSON），支持复杂查询

### 缺点

- 信息量取决于埋点质量——日志打得不好就查不到关键信息
- 无法交互式调试
- 远程收集需要网络基础设施

### 最佳实践

```python
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        # 附加额外上下文
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)
```

---

## 方案四：远程 REPL / RPC 诊断

### 原理

```
目标机器                              开发者
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe              │            │ 终端 / 诊断工具      │
│                      │            │                     │
│ 内嵌 RPC 服务:       │  加密连接   │ > get_memory_usage()│
│   get_memory_usage() │◄──────────│ > get_db_pool_status│
│   get_db_pool_status │            │ > set_log_level()   │
│   dump_state()       │            │ > dump_state()      │
│   set_log_level()    │            │                     │
└──────────────────────┘            └─────────────────────┘
```

### 关键技术点

- 在客户端中内嵌一个轻量级 RPC 服务，只暴露**预定义的诊断函数**
- 开发者可以远程调用这些函数获取运行时状态，但**无法执行任意代码、无法看到源码**
- 常用库：`rpyc`、`xmlrpc`、`gRPC`，或基于 WebSocket 的自定义协议

### 示例代码

```python
# ========== 客户端（被诊断端）==========
import threading
from xmlrpc.server import SimpleXMLRPCServer

class DiagnosticService:
    def get_memory_usage(self):
        import psutil
        proc = psutil.Process()
        return {
            "rss_mb": proc.memory_info().rss / 1024 / 1024,
            "vms_mb": proc.memory_info().vms / 1024 / 1024,
        }

    def get_db_connection_count(self):
        return db.get_pool_status()

    def get_app_state(self):
        return {
            "version": APP_VERSION,
            "uptime_seconds": time.time() - START_TIME,
            "current_user": current_user.username if current_user else None,
        }

    def set_log_level(self, level):
        logging.getLogger().setLevel(getattr(logging, level.upper()))
        return f"日志级别已设置为 {level}"

def start_diagnostic_server(port=9999):
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True)
    server.register_instance(DiagnosticService())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


# ========== 开发者端（诊断端）==========
import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://target-ip:9999")
print(proxy.get_memory_usage())        # {'rss_mb': 45.2, 'vms_mb': 120.5}
print(proxy.get_db_connection_count())  # {'active': 3, 'idle': 7}
print(proxy.set_log_level('DEBUG'))     # 日志级别已设置为 DEBUG
```

### 优点

- **完全不暴露源码**
- 可在生产环境安全使用（只暴露预定义接口）
- 实时交互，按需获取信息
- 可以动态调整运行时参数（如日志级别、缓存开关）

### 缺点

- 需要开发诊断接口，有一定工作量
- 不能设断点，不能单步执行
- 需要网络直连
- 需要考虑安全性（认证、加密、访问控制）

### 安全建议

```python
# 1. 只在特定启动参数下开启
if args.diagnostic:
    start_diagnostic_server()

# 2. 加入 token 认证
def authenticated(func):
    def wrapper(token, *args, **kwargs):
        if token != os.environ.get('DIAG_TOKEN'):
            raise PermissionError("Invalid token")
        return func(*args, **kwargs)
    return wrapper

# 3. 只监听 localhost（需要 SSH 隧道才能远程访问）
server = SimpleXMLRPCServer(('127.0.0.1', 9999))
```

---

## 方案五：条件性源码映射

### 原理

```
目标机器                              开发者机器
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe --debug      │            │ VSCode              │
│                      │ 5678       │   Attach             │
│ debugpy.listen()     │◄───────────│                     │
│                      │            │ 源码通过网络共享      │
│ 本地无 .py 文件       │            │ 挂载到目标机器        │
│ 但 debugpy 读取       │            │ \\dev-pc\src\        │
│ 网络共享的源码        │            │                     │
└──────────────────────┘            └─────────────────────┘
```

### 关键技术点

- exe 中**不打入源码**，保持 Release 版的安全性
- 调试时由开发者通过**网络共享/SSH/远程桌面**将 `src/` 目录临时挂载到目标机器
- debugpy 通过 `pathMappings` 或 `setup_client_server_paths` 映射到挂载路径
- 调试完毕后断开共享，源码不残留在目标机器

### 优点

- 源码不打包进 exe，不会永久暴露
- 保留完整的交互式调试能力

### 缺点

- 操作复杂，需要网络共享环境
- 目标机器需要安装 Python + debugpy（无法用线程模式 adapter，因为没有源码来做字节码校验）
- 仅适合内网环境

---

## 方案六：核心转储 + 离线分析

### 原理

```
目标机器                              开发者机器
┌──────────────────────┐            ┌─────────────────────┐
│ app.exe              │            │                     │
│                      │  传输文件   │ 分析工具            │
│ 崩溃! →              │──────────►│ crash_dump.dmp      │
│   生成 crash_dump    │            │ + 源码 + 符号表      │
│   + traceback.txt    │            │ → 还原崩溃现场       │
│                      │            │                     │
└──────────────────────┘            └─────────────────────┘
```

### 关键技术点

- 在客户端中注册全局异常处理器，崩溃时自动保存：
  - Python traceback 文本
  - 关键变量快照
  - （可选）Windows minidump 文件
- 用户将生成的 dump 文件发送给开发者
- 开发者在本地结合源码分析崩溃原因

### 示例代码

```python
import sys
import traceback
import json
from datetime import datetime

def crash_handler(exc_type, exc_value, exc_tb):
    """全局崩溃处理器"""
    crash_info = {
        "timestamp": datetime.now().isoformat(),
        "exception_type": exc_type.__name__,
        "exception_message": str(exc_value),
        "traceback": traceback.format_exception(exc_type, exc_value, exc_tb),
        "python_version": sys.version,
        "platform": sys.platform,
    }

    # 保存到文件
    crash_file = f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(crash_file, 'w', encoding='utf-8') as f:
        json.dump(crash_info, f, ensure_ascii=False, indent=2)

    print(f"程序崩溃，错误信息已保存到 {crash_file}")
    print("请将此文件发送给开发团队以协助排查问题。")

# 注册全局异常处理器
sys.excepthook = crash_handler
```

### 优点

- 完全不暴露源码
- 无需网络连接（离线生成 dump）
- 适合难以复现的偶发崩溃
- 生产环境安全使用

### 缺点

- 只能分析崩溃场景，无法诊断非崩溃 bug
- 信息量有限（只有崩溃瞬间的快照）
- 依赖用户配合发送文件

---

## 方案选型指南

### 按项目阶段推荐

```
开发阶段 ──────► ① debugpy（断点调试，快速定位问题）
    │
内测阶段 ──────► ① debugpy + ② Sentry + ③ 日志
    │              (团队内调试)  (自动上报)  (事后分析)
    │
生产阶段 ──────► ② Sentry + ③ 日志 + ⑥ 核心转储
                  (异常监控)  (日志分析)  (崩溃分析)
    │
    └─ 高级需求 ─► ④ RPC 诊断（实时诊断运行状态）
```

### 按团队规模推荐

| 团队规模          | 推荐组合                                       |
| ----------------- | ---------------------------------------------- |
| 个人开发          | ① debugpy + ⑥ 核心转储                         |
| 小团队（3-10 人） | ① debugpy + ② Sentry + ③ 本地日志              |
| 中型团队          | ① debugpy + ② Sentry + ③ ELK/Loki + ④ RPC 诊断 |
| 大型团队          | 全部方案按需组合                               |

### 按安全要求推荐

| 安全要求         | 可用方案                    |
| ---------------- | --------------------------- |
| 源码绝对不能泄露 | ②③④⑥（完全不涉及源码）      |
| 内网可控环境     | 所有方案                    |
| 面向公众发布     | ②③⑥（被动收集，无远程接口） |

---

## 本项目当前实现

本项目采用 **方案一（debugpy 远程调试）**，通过 `build.bat` 区分构建模式：

- **Debug 版**（`build.bat`）：带源码 + debugpy，支持 `--debug` 远程调试，用于开发和内测
- **Release 版**（`build.bat --release`）：不带源码，排除 debugpy，用于正式发布

详细使用方法参见 [README.md](../README.md) 的「远程调试」章节。
