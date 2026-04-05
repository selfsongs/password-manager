# 本地密码管理器

基于 Python + customtkinter 的本地密码管理客户端，支持多用户登录注册，所有密码均加密存储在本地数据库中。支持 SQLite / MySQL / PostgreSQL / MongoDB 多后端切换，可选 Redis 缓存加速。

## 项目结构

   ```bash
my-demo-project/
├── src/
│   ├── main.py         # 入口，App 主窗口
│   ├── database.py     # 数据库统一接口层（对外 API 不变，集成缓存）
│   ├── db_backend.py   # 数据库后端抽象基类
│   ├── db_config.py    # 配置管理（读取 db_config.json，创建后端实例）
│   ├── db_sqlite.py    # SQLite 后端实现
│   ├── db_mysql.py     # MySQL 后端实现
│   ├── db_mongodb.py   # MongoDB 后端实现
│   ├── db_postgresql.py # PostgreSQL 后端实现
│   ├── redis_cache.py  # Redis 缓存层（可选，配合数据库后端使用）
│   ├── crypto.py       # 加密模块（bcrypt + AES-256）
│   ├── auth_view.py    # 登录/注册界面
│   └── main_view.py    # 主界面（列表、搜索、添加、编辑、删除）
├── data/
│   └── passwords.db    # SQLite 数据库文件（自动生成）
├── db_config.json      # 数据库 & 缓存配置文件
├── requirements.txt
└── README.md
```

## 快速开始

### 选项 1：使用传统 pip（推荐给不熟悉 uv 的用户）

1. 创建并激活虚拟环境：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

1. 安装依赖：

```bash
pip install -r requirements.txt
```

1. 运行：

```bash
python src/main.py
```

1. 结束后退出虚拟环境：

```bash
deactivate
```

### 选项 2：使用 uv（推荐，速度更快）

1. 安装 uv（如果尚未安装）：

```bash
pip install uv
```

1. 创建虚拟环境并激活：

```bash
uv venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

1. 安装依赖：

```bash
uv pip install -r requirements.txt

# 如果这个项目配置了pyproject.toml，也可以使用uv sync来安装依赖。
uv sync

# 查看已安装依赖
uv pip list
```

1. 运行：

```bash
python src/main.py
```

1. 结束后退出虚拟环境：

```bash
deactivate
```

## 数据库配置

项目支持多种数据库后端，通过项目根目录的 `db_config.json` 配置切换，**无需修改任何业务代码**。

### 使用 SQLite（默认）

```json
{
    "type": "sqlite",
    "sqlite": {
        "db_path": ""
    }
}
```

`db_path` 为空时默认使用 `data/passwords.db`，也可指定绝对路径。

### 使用 MySQL

1. 安装 MySQL 驱动：

```bash
pip install pymysql
```

1. 修改 `db_config.json`：

```json
{
    "type": "mysql",
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "your_password",
        "database": "password_manager"
    }
}
```

数据库会自动创建（如果不存在）。

### 使用 MongoDB

1. 安装 MongoDB 驱动：

```bash
pip install pymongo
```

1. 修改 `db_config.json`：

```json
{
    "type": "mongodb",
    "mongodb": {
        "host": "127.0.0.1",
        "port": 27017,
        "username": "",
        "password": "",
        "database": "password_manager",
        "auth_source": "admin"
    }
}
```

| 配置项        | 说明                 | 默认值             |
| ------------- | -------------------- | ------------------ |
| `host`        | MongoDB 服务器地址   | `127.0.0.1`        |
| `port`        | MongoDB 端口         | `27017`            |
| `username`    | 用户名，无认证时留空 | `""`               |
| `password`    | 密码，无认证时留空   | `""`               |
| `database`    | 数据库名             | `password_manager` |
| `auth_source` | 认证数据库           | `admin`            |

MongoDB 不需要预先建库建表——数据库和集合（collection）在首次写入时自动创建，`init_db()` 只会创建必要的索引。

> **关于自增 ID：** MongoDB 原生主键是 `ObjectId`（字符串），但为了与 SQLite/MySQL 的接口保持一致（返回 `int` 类型 ID），采用了 MongoDB 官方推荐的计数器模式——通过 `counters` 集合原子递增来生成自增 ID。

### 使用 PostgreSQL

1. 安装 PostgreSQL 驱动：

```bash
pip install psycopg2-binary
```

1. 修改 `db_config.json`：

```json
{
    "type": "postgresql",
    "postgresql": {
        "host": "127.0.0.1",
        "port": 5432,
        "user": "postgres",
        "password": "your_password",
        "database": "password_manager"
    }
}
```

| 配置项     | 说明                  | 默认值             |
| ---------- | --------------------- | ------------------ |
| `host`     | PostgreSQL 服务器地址 | `127.0.0.1`        |
| `port`     | PostgreSQL 端口       | `5432`             |
| `user`     | 用户名                | `postgres`         |
| `password` | 密码                  | `""`               |
| `database` | 数据库名              | `password_manager` |

数据库会自动创建（如果不存在）。PostgreSQL 使用 `SERIAL` 类型实现自增主键，`RETURNING id` 获取插入后的 ID，并通过触发器自动更新 `updated_at` 字段。

### Redis 缓存（可选）

Redis 作为**缓存层**配合数据库后端使用，加速热数据读取。它不是数据库后端的替代品，而是独立的辅助层。

> **为什么 Redis 不作为 `DatabaseBackend` 的实现？**  
> `DatabaseBackend` 抽象基类是为关系型数据库设计的（表、行、自增 ID、外键），SQLite 和 MySQL 都符合这一模型。Redis 是 Key-Value 内存数据库，数据模型完全不同，强行统一接口会削足适履。正确的做法是让 Redis 发挥它真正的优势——**缓存、会话管理、计数器**，与数据库分层配合使用。

1. 安装 Redis 客户端库：

```bash
pip install redis
```

1. 在 `db_config.json` 中启用 Redis：

```json
{
    "type": "sqlite",
    "redis": {
        "enabled": true,
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0,
        "password": "",
        "default_ttl": 300
    }
}
```

| 配置项        | 说明                     | 默认值         |
| ------------- | ------------------------ | -------------- |
| `enabled`     | 是否启用 Redis 缓存      | `false`        |
| `host`        | Redis 服务器地址         | `127.0.0.1`    |
| `port`        | Redis 端口               | `6379`         |
| `db`          | Redis 数据库编号（0-15） | `0`            |
| `password`    | Redis 密码，无密码留空   | `""`           |
| `default_ttl` | 默认缓存过期时间（秒）   | `300`（5分钟） |

#### Redis 缓存层提供的功能

| 功能         | 方法                                                     | 说明                                   |
| ------------ | -------------------------------------------------------- | -------------------------------------- |
| 密码条目缓存 | `cache_passwords` / `get_cached_passwords`               | 减少数据库查询，自动过期               |
| 用户信息缓存 | `cache_user` / `get_cached_user`                         | 缓存频繁查询的用户信息                 |
| 缓存失效     | `invalidate_passwords` / `invalidate_user`               | 数据变更时主动清除缓存                 |
| 会话管理     | `set_session` / `get_session` / `delete_session`         | Token ↔ user_id 映射，支持过期（预留） |
| 登录防护     | `incr_login_fail` / `is_locked_out` / `reset_login_fail` | 失败计数，防暴力破解（预留）           |

其中密码条目缓存和用户信息缓存已集成到 `database.py` 中自动工作；会话管理和登录防护为预留能力，可通过 `db.get_cache()` 获取实例后在业务层使用。

#### 缓存工作流程

```
读取密码列表：
  database.get_passwords(user_id)
       │
       ▼
  Redis 有缓存？ ──是──► 直接返回（快）
       │
       否
       │
       ▼
  查询数据库 ──► 回填 Redis 缓存 ──► 返回结果

写入/更新/删除密码：
  database.add_password / update_password / delete_password
       │
       ▼
  写入数据库 ──► 清除该用户的 Redis 缓存（保证一致性）
```

#### 降级机制

**Redis 不可用时，系统自动降级为纯数据库模式，不影响任何功能。** 具体表现：

- `db_config.json` 中 `enabled` 为 `false`（默认）：不会尝试连接 Redis
- `enabled` 为 `true` 但 Redis 服务未运行：连接失败后自动降级，控制台提示 `[缓存] Redis 连接失败，将以纯数据库模式运行`
- 未安装 `redis` Python 包：初始化时捕获 `ImportError`，自动降级

### 架构图

```
                            db_config.json
                                 │
                                 ▼
                            db_config.py ──► create_backend()
                                 │
        ┌────────────────┬───────────────────┬──────────────────┐
        ▼                ▼                   ▼                  ▼
   SQLiteBackend   MySQLBackend    PostgreSQLBackend    MongoDBBackend
        │                │                   │                  │
        └────────────────┴───────────────────┴──────────────────┘
                                 ▼
                        DatabaseBackend (抽象基类)
                                 ▲
                                 │
  RedisCache ◄──────────► database.py (代理层，集成缓存)
  (可选缓存层)                   ▲
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
               auth_view    main_view      main.py
               (零改动)     (零改动)       (零改动)
```

切换数据库只需修改 `db_config.json` 中的 `"type"` 字段即可，业务代码完全无感。Redis 缓存通过 `"redis.enabled"` 独立控制。

### 扩展其他关系型数据库

添加新的数据库支持只需三步：

1. 新建 `src/db_xxx.py`，继承 `DatabaseBackend` 并实现所有抽象方法
2. 在 `src/db_config.py` 的 `create_backend()` 中添加对应的分支
3. 在 `db_config.json` 中添加对应的配置项

## 功能列表

| 功能             | 说明                                                      |
| ---------------- | --------------------------------------------------------- |
| 多用户注册/登录  | bcrypt 哈希校验主密码                                     |
| AES-256 加密存储 | 账号和密码字段均加密保存                                  |
| 密码列表         | 按网站名排序，展示账号                                    |
| 实时搜索         | 按网站名/网址/账号过滤                                    |
| 添加/编辑/删除   | 完整 CRUD                                                 |
| 一键复制密码     | 解密后复制到剪贴板                                        |
| 随机密码生成     | 16位，含大小写+数字+符号（使用 secrets 模块，密码学安全） |
| 退出登录         | 返回登录界面                                              |

### 搜索机制说明

由于账号字段在数据库中是 AES 加密存储的，无法通过 SQL `LIKE` 直接匹配密文。因此搜索采用**应用层过滤**策略：

1. 从数据库获取当前用户的所有密码条目
2. 对明文字段（网站名称、网址）直接进行关键词匹配
3. 对加密字段（账号）先解密再进行关键词匹配
4. 搜索不区分大小写

### 密码生成器

随机密码生成使用 Python 标准库 `secrets` 模块（而非 `random`），确保生成的随机数具备**密码学安全性**，不可被预测。生成的 16 位密码包含大小写字母、数字和特殊符号，并保证每种字符类型至少出现一次。

---

## 安全设计说明

### 两套独立的安全机制

本项目使用两套完全独立的机制，分别承担不同职责：

**机制一：bcrypt —— 验证主密码是否正确**

```
注册时：主密码明文  ──► bcrypt ──► password_hash ──► 存入数据库
登录时：输入的密码  ──► bcrypt 验证 ──► 与数据库 hash 比对 ──► 通过/拒绝
```

bcrypt 是单向哈希，`password_hash` 无法反推出原始主密码，仅用于"门卫验证"。

**机制二：PBKDF2 + AES-256 —— 加密/解密存储的密码条目**

```
添加密码时：主密码明文 + salt ──► PBKDF2（48万次迭代）──► AES密钥 ──► 加密 ──► 密文存数据库
读取密码时：主密码明文 + salt ──► PBKDF2（同样参数） ──► AES密钥 ──► 解密 ──► 显示明文
```

PBKDF2 的输入是**主密码明文**（不是 password_hash），相同的主密码 + salt 每次都能派生出完全相同的 AES 密钥，这是可逆解密的基础。

### 为什么 AES 能加密又能解密？

AES 是**对称加密**，同一把密钥既加密也解密：

```
对称加密（AES）：  同一密钥 ──► 加密/解密    速度快，适合大量数据
非对称加密（RSA）：公钥加密，私钥解密        适合身份验证/密钥交换
```

本项目选用 AES-256（密钥长度 256 位），目前没有已知的实际破解方法。

### salt 的作用

`salt` 是注册时生成的随机字符串，明文存储在 `users` 表中。它的作用是防止彩虹表攻击——即使两个用户使用相同的主密码，因为 salt 不同，派生出的 AES 密钥也完全不同。**单独拿到 salt 而没有主密码明文，无法派生出密钥。**

### PBKDF2 的 48 万次迭代

故意让每次密钥派生都消耗较长时间，使暴力枚举主密码的成本极高，即使数据库泄露也难以破解。

### 数据库实际存储的内容

```
users 表
┌──────────┬────────────────────┬───────────────┐
│ username │ password_hash      │ salt          │
├──────────┼────────────────────┼───────────────┤
│ alice    │ $2b$12$xxx...      │ base64随机串  │
└──────────┴────────────────────┴───────────────┘

passwords 表
┌───────────┬──────────────────────────────┐
│ site_name │ password（密文）              │
├───────────┼──────────────────────────────┤
│ GitHub    │ gAAAAABpu6w2wkc3xjav...      │
└───────────┴──────────────────────────────┘
```

数据库中没有任何明文密码，也没有 AES 密钥。

### 各攻击场景下的安全性

| 攻击场景       | 结果                                |
| -------------- | ----------------------------------- |
| 数据库文件被盗 | 只有密文和 salt，没有主密码无法解密 |
| 不知道主密码   | 无法派生 AES 密钥，无法解密         |
| 主密码忘记     | 数据永久无法恢复（这是正确设计）    |
| 程序关闭       | 内存中的主密码和密钥随进程消失      |

### 安全瓶颈

整套系统的安全性最终取决于**主密码的强度**。主密码越复杂，暴力破解成本越高，数据越安全。

---

## 打包分发与依赖说明

### 打包方式对比

| 打包工具        | 输出格式          | 用途                | 适用场景               |
| --------------- | ----------------- | ------------------- | ---------------------- |
| **uv**          | whl 文件          | 打包成 Python 包/库 | 分发包给其他开发者使用 |
| **PyInstaller** | 可执行文件 (.exe) | 打包成独立应用程序  | 分发给最终用户直接运行 |

### 如何区分 Python 项目应该打包成库还是可执行文件

#### 适合打包成 Python 包/库（whl）的情况

当项目符合以下特征时，适合打包成库：

1. **可重用性**：项目提供了可在其他项目中重用的功能或模块
2. **API 导向**：项目设计为通过导入和调用其 API 来使用
3. **无 GUI**：项目主要是后台功能，没有图形界面
4. **开发者工具**：项目是为其他开发者提供的工具或组件
5. **示例**：
   - 一个处理日期时间的库
   - 一个网络请求库
   - 一个数据分析工具包

#### 适合打包成可执行文件（exe）的情况

当项目符合以下特征时，适合打包成可执行文件：

1. **独立应用**：项目是一个完整的应用程序，有自己的用户界面
2. **最终用户导向**：项目面向普通用户，而非开发者
3. **特定功能**：项目实现了一个特定的功能，如密码管理、文件转换等
4. **自包含**：项目需要包含所有依赖，无需用户额外安装
5. **示例**：
   - 桌面应用程序（如密码管理器）
   - 命令行工具
   - 游戏或其他交互式应用

#### 本项目的打包建议

对于当前的密码管理器项目，**推荐使用 PyInstaller 打包成可执行文件**，因为：

1. **用户友好**：最终用户可以直接双击运行，无需了解 Python
2. **依赖完整**：所有依赖（包括 customtkinter、cryptography 等）都会被打包
3. **配置灵活**：通过外部配置文件，用户可以灵活修改数据库设置
4. **安全可靠**：作为独立应用，减少了外部依赖带来的安全风险

### 使用 uv 打包成 whl 文件

whl (Wheel) 是 Python 的二进制包格式，用于分发包和库。使用 uv 打包成 whl 文件的步骤：

1. **确保项目结构正确**：

   ```
   password_manager/
   ├── src/
   │   └── password_manager/  # 包目录
   │       ├── __init__.py
   │       ├── main.py
   │       └── ...
   ├── pyproject.toml
   └── ...
   ```

2. **创建 pyproject.toml 文件**：

   ```toml
   [project]
   name = "password-manager"
   version = "0.1.0"
   description = "本地密码管理器"
   authors = [
       { name = "Your Name", email = "your.email@example.com" },
   ]
   dependencies = [
       "customtkinter>=5.2.0",
       "cryptography>=41.0.0",
       "bcrypt>=4.0.0",
   ]

   [build-system]
   requires = ["setuptools", "wheel"]
   build-backend = "setuptools.build_meta"
   ```

3. **使用 uv 构建 whl 文件**：

   ```bash
   uv build
   ```

4. **安装 whl 文件**：

   ```bash
   pip install dist/password_manager-0.1.0-py3-none-any.whl
   ```

### 使用 PyInstaller 打包

本项目支持使用 PyInstaller 打包为可执行文件，方便分发给其他用户。以下是详细的打包指南：

#### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

#### 2. 单文件打包（--onefile）

```bash
# 1.执行打包命令：
pyinstaller --onefile --name password_manager src/main.py

# 2. 复制配置文件： 将 db_config.json 文件复制到生成的 dist/password_manager 目录中。

# 3.分发整个目录： 将整个 dist/password_manager 目录压缩后分发给其他用户，或直接复制整个目录。

# 4. 用户使用： 用户解压后，直接运行目录中的 password_manager.exe 即可。
```

**特点：**

- 生成一个单独的可执行文件（.exe）
- 所有依赖和 DLL 文件都被打包到这个单一的文件中
- 运行时会临时解压到临时目录，然后执行
- 优点：分发方便，只有一个文件
- 缺点：启动速度较慢，因为每次运行都需要解压

#### 3. 非单文件打包（默认）

```bash
# 1.执行打包命令：
pyinstaller --name password_manager src/main.py

# 2. 复制配置文件： 将 db_config.json 文件复制到生成的 dist/password_manager 目录中。

# 3.分发整个目录： 将整个 dist/password_manager 目录压缩后分发给其他用户，或直接复制整个目录。

# 4. 用户使用： 用户解压后，直接运行目录中的 password_manager.exe 即可。

# 5. 便于调试，在dist中添加一个批处理文件，用于创建日志
# 在 dist/password_manager 目录中创建一个批处理文件（例如 run_with_log.bat），编辑批处理文件，添加以下内容：
@echo off
password_manager.exe > log.txt 2>&1
pause
```

**特点：**

- 生成一个包含可执行文件和多个 DLL 文件的目录
- 依赖的 DLL 文件会被复制到生成的目录中
- 直接从目录中加载 DLL 文件，不需要解压
- 优点：启动速度快，文件结构清晰
- 缺点：分发时需要整个目录，不如单文件模式方便

### 虚拟环境打包与系统环境打包的区别

#### 在虚拟环境中打包（推荐）

**步骤：**

1. **激活虚拟环境**：

   ```bash
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **在虚拟环境中安装 PyInstaller**：

   ```bash
   # 使用 pip
   pip install pyinstaller
   # 或使用 uv
   uv pip install pyinstaller
   ```

3. **运行打包命令**：

   ```bash
   pyinstaller --name password_manager src/main.py
   ```

**优点：**

- 只打包虚拟环境中安装的依赖，避免打包系统中不必要的包
- 依赖版本可控，与开发环境一致
- 减少打包文件大小
- 避免依赖冲突

#### 不在虚拟环境中打包（不推荐）

**步骤：**

1. **直接安装 PyInstaller**：

   ```bash
   pip install pyinstaller
   ```

2. **运行打包命令**：

   ```bash
   pyinstaller --name password_manager src/main.py
   ```

**缺点：**

- 可能打包系统中所有已安装的依赖，导致打包文件过大
- 依赖版本可能与开发环境不一致
- 容易出现依赖冲突
- 可能包含不必要的包，影响程序运行

#### 4. 配置文件处理

无论使用哪种打包方式，程序都会优先查找外部配置文件：

- **未打包时**：使用项目根目录的 `db_config.json`
- **打包后**：使用可执行文件同目录的 `db_config.json`

**注意：** 打包后，需要将 `db_config.json` 文件复制到可执行文件所在目录，以便用户可以修改配置。

#### 5. 打包命令示例

```bash
# 单文件模式，添加图标
pyinstaller --onefile --name password_manager --icon=icon.ico src/main.py

# 非单文件模式
pyinstaller --name password_manager src/main.py
```

### 6. 使用 build.bat 脚本自动化打包（推荐）

项目根目录提供了 `build.bat` 脚本，可以一键完成整个打包流程，包括：

- 检查并创建虚拟环境
- 激活虚拟环境
- 安装依赖
- 安装 PyInstaller
- 执行打包
- 复制配置文件
- 创建运行脚本
- 创建压缩包用于分发

#### 使用方法

```bash
# 使用传统 pip 安装依赖
build.bat

# 使用 uv 安装依赖（速度更快）
build.bat --uv
```

#### 脚本功能

1. **自动检查 uv**：如果使用 `--uv` 参数，会自动检查并安装 uv
2. **虚拟环境管理**：自动创建和激活虚拟环境
3. **依赖安装**：根据选择的工具（pip 或 uv）安装依赖
4. **打包执行**：使用 PyInstaller 执行非单文件打包
5. **配置文件处理**：自动复制 db_config.json 到打包目录
6. **运行脚本创建**：创建 run_with_log.bat 用于运行程序并记录日志
7. **压缩包创建**：将打包后的目录压缩为 zip 文件，方便分发

#### 输出结果

执行完成后，会在 `dist` 目录中生成：

- `password_manager` 目录：包含可执行文件和依赖
- `password_manager.zip`：用于分发的压缩包

将程序打包（如使用 PyInstaller）分发给其他用户时，需要了解各依赖的情况：

### 依赖一览

| 依赖                  | 类型                    | 打包时是否包含 | 对方是否需要额外安装       |
| --------------------- | ----------------------- | :------------: | -------------------------- |
| `sqlite3`             | Python 标准库           |   ✅ 自动包含   | ❌ **不需要**，Python 内置  |
| `debugpy`             | Python 包（调试工具）   |  ✅ 打包时带入  | ❌ 不需要单独安装           |
| `pymysql`             | Python 包（客户端驱动） |  ✅ 打包时带入  | ❌ 不需要单独安装           |
| `redis`               | Python 包（客户端驱动） |  ✅ 打包时带入  | ❌ 不需要单独安装           |
| `pymongo`             | Python 包（客户端驱动） |  ✅ 打包时带入  | ❌ 不需要单独安装           |
| `psycopg2-binary`     | Python 包（客户端驱动） |  ✅ 打包时带入  | ❌ 不需要单独安装           |
| **MySQL Server**      | 独立服务                |   ❌ 无法打包   | ⚠️ 选 MySQL 模式时需要      |
| **PostgreSQL Server** | 独立服务                |   ❌ 无法打包   | ⚠️ 选 PostgreSQL 模式时需要 |
| **MongoDB Server**    | 独立服务                |   ❌ 无法打包   | ⚠️ 选 MongoDB 模式时需要    |
| **Redis Server**      | 独立服务                |   ❌ 无法打包   | ⚠️ 启用 Redis 缓存时需要    |

### 关键区别：Python 包 vs 服务

```
pymysql / psycopg2 / pymongo / redis（Python 包）= 遥控器     → 打包时可以带上
MySQL / PostgreSQL / MongoDB / Redis Server       = 电视机/空调 → 需要对方自己安装
```

- **Python 包**（`pymysql`、`psycopg2-binary`、`pymongo`、`redis`）只是客户端驱动，负责与服务器通信，可以随程序一起打包
- **数据库/缓存服务**（MySQL、PostgreSQL、MongoDB、Redis Server）是独立运行的服务进程，无法打包进应用程序

### 默认配置下的兼容性

**默认配置（SQLite + Redis 关闭）下，打包后发给任何人都能直接运行**，无需安装任何额外软件：

- SQLite 是嵌入式数据库，引擎内置于 Python 中，数据存储为本地 `.db` 文件
- Redis 缓存默认关闭（`"enabled": false`），即使对方没有 Redis 也完全不影响使用

### 各场景说明

| 使用场景                | 对方需要做什么                              | 难度  |
| ----------------------- | ------------------------------------------- | :---: |
| **SQLite 模式（默认）** | 无需任何操作，开箱即用                      |   ⭐   |
| **MySQL 模式**          | 需自行安装 MySQL Server 并配置连接信息      |  ⭐⭐⭐  |
| **PostgreSQL 模式**     | 需自行安装 PostgreSQL Server 并配置连接信息 |  ⭐⭐⭐  |
| **MongoDB 模式**        | 需自行安装 MongoDB Server 并配置连接信息    |  ⭐⭐⭐  |
| **启用 Redis 缓存**     | 需自行安装 Redis Server 并配置连接信息      |  ⭐⭐⭐  |
| **数据库 + Redis**      | 需安装两个服务并分别配置                    | ⭐⭐⭐⭐  |

> **建议**：面向普通用户分发时保持默认 SQLite 配置即可。MySQL、PostgreSQL、MongoDB 和 Redis 是面向有技术背景的用户或服务器部署场景的可选高级功能。