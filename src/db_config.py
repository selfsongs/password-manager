"""
db_config.py - 数据库配置管理
从 db_config.json 读取配置，创建对应的数据库后端实例。
"""

import json
import sys
from pathlib import Path

from db_backend import DatabaseBackend

# 配置文件路径：项目根目录 db_config.json
CONFIG_PATH = Path(__file__).parent.parent / "db_config.json"

# 外部配置文件路径（打包后使用）
if hasattr(sys, '_MEIPASS'):
    EXTERNAL_CONFIG_PATH = Path(sys.executable).parent / "db_config.json"
else:
    EXTERNAL_CONFIG_PATH = CONFIG_PATH

# 默认配置（SQLite + 可选 Redis 缓存）
DEFAULT_CONFIG = {
    "type": "sqlite",
    "sqlite": {
        "db_path": ""  # 为空则使用默认路径 data/passwords.db
    },
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "password_manager",
    },
    "redis": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0,
        "password": "",
        "default_ttl": 300,  # 缓存过期时间（秒）
    },
    "mongodb": {
        "host": "127.0.0.1",
        "port": 27017,
        "username": "",
        "password": "",
        "database": "password_manager",
        "auth_source": "admin",
    },
    "postgresql": {
        "host": "127.0.0.1",
        "port": 5432,
        "user": "postgres",
        "password": "",
        "database": "password_manager",
    },
}


def load_config() -> dict:
    """加载数据库配置，配置文件不存在时自动生成默认配置"""
    # 优先查找外部配置文件（打包后在可执行文件同目录）
    if EXTERNAL_CONFIG_PATH.exists():
        with open(EXTERNAL_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # 其次查找项目根目录的配置文件
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """保存配置到文件"""
    # 优先保存到外部配置文件（打包后在可执行文件同目录）
    target_path = EXTERNAL_CONFIG_PATH if EXTERNAL_CONFIG_PATH.exists() else CONFIG_PATH
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def create_backend(config: dict | None = None) -> DatabaseBackend:
    """
    根据配置创建数据库后端实例。

    支持的类型：
      - "sqlite"：SQLite 本地数据库（默认）
      - "mysql"：MySQL 数据库（需安装 pymysql）

    扩展新数据库时，只需：
      1. 新建 db_xxx.py 实现 DatabaseBackend
      2. 在此函数中添加对应的分支
    """
    if config is None:
        config = load_config()

    db_type = config.get("type", "sqlite").lower()

    if db_type == "sqlite":
        from db_sqlite import SQLiteBackend

        sqlite_conf = config.get("sqlite", {})
        db_path = sqlite_conf.get("db_path", "") or None
        return SQLiteBackend(db_path=db_path)

    elif db_type == "mysql":
        from db_mysql import MySQLBackend

        mysql_conf = config.get("mysql", {})
        return MySQLBackend(
            host=mysql_conf.get("host", "127.0.0.1"),
            port=mysql_conf.get("port", 3306),
            user=mysql_conf.get("user", "root"),
            password=mysql_conf.get("password", ""),
            database=mysql_conf.get("database", "password_manager"),
        )

    elif db_type == "mongodb":
        from db_mongodb import MongoDBBackend

        mongo_conf = config.get("mongodb", {})
        return MongoDBBackend(
            host=mongo_conf.get("host", "127.0.0.1"),
            port=mongo_conf.get("port", 27017),
            username=mongo_conf.get("username", ""),
            password=mongo_conf.get("password", ""),
            database=mongo_conf.get("database", "password_manager"),
            auth_source=mongo_conf.get("auth_source", "admin"),
        )

    elif db_type == "postgresql":
        from db_postgresql import PostgreSQLBackend

        pg_conf = config.get("postgresql", {})
        return PostgreSQLBackend(
            host=pg_conf.get("host", "127.0.0.1"),
            port=pg_conf.get("port", 5432),
            user=pg_conf.get("user", "postgres"),
            password=pg_conf.get("password", ""),
            database=pg_conf.get("database", "password_manager"),
        )

    else:
        raise ValueError(
            f"不支持的数据库类型：'{db_type}'。"
            f"目前支持：sqlite, mysql, mongodb, postgresql"
        )
