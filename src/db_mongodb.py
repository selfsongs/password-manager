"""
db_mongodb.py - MongoDB 数据库后端实现
需要安装依赖：pip install pymongo
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db_backend import DatabaseBackend, RowDict

try:
    from pymongo import MongoClient, ASCENDING
    from pymongo.collection import Collection, ReturnDocument
except ImportError:
    MongoClient = None  # type: ignore


class MongoDBBackend(DatabaseBackend):
    """MongoDB 数据库后端"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27017,
        username: str = "",
        password: str = "",
        database: str = "password_manager",
        auth_source: str = "admin",
    ):
        if MongoClient is None:
            raise ImportError(
                "MongoDB 后端需要 pymongo 库，请运行：pip install pymongo"
            )

        # 构建连接参数
        if username and password:
            self._client = MongoClient(
                host=host,
                port=port,
                username=username,
                password=password,
                authSource=auth_source,
            )
        else:
            self._client = MongoClient(host=host, port=port)

        self.db = self._client[database]
        self._users: Collection = self.db["users"]
        self._passwords: Collection = self.db["passwords"]
        self._counters: Collection = self.db["counters"]

    # ==========================================================
    #  自增 ID 管理（MongoDB 官方推荐模式）
    # ==========================================================

    def _next_id(self, collection_name: str) -> int:
        """原子递增并返回下一个自增 ID。

        使用 counters 集合存储每个集合的当前最大 ID，
        通过 find_one_and_update 的原子操作保证并发安全。
        """
        result = self._counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(result["seq"])

    # ==========================================================
    #  生命周期
    # ==========================================================

    def init_db(self) -> None:
        """初始化数据库，创建索引。

        MongoDB 不需要预先建表（集合自动创建），
        但需要建索引以保证查询性能和唯一性约束。
        """
        # users 集合：username 唯一索引
        self._users.create_index(
            [("username", ASCENDING)], unique=True, name="idx_username_unique"
        )
        # passwords 集合：user_id 索引（加速按用户查询）
        self._passwords.create_index(
            [("user_id", ASCENDING)], name="idx_user_id"
        )
        # passwords 集合：id 唯一索引
        self._passwords.create_index(
            [("id", ASCENDING)], unique=True, name="idx_password_id_unique"
        )

    def close(self) -> None:
        """关闭 MongoDB 连接"""
        self._client.close()

    # ==========================================================
    #  内部工具方法
    # ==========================================================

    @staticmethod
    def _clean_doc(doc: dict[str, Any] | None) -> RowDict | None:
        """清理 MongoDB 文档，移除 _id 字段，使返回格式与 SQLite/MySQL 一致。"""
        if doc is None:
            return None
        doc.pop("_id", None)
        # 将 datetime 转为字符串，保持和 SQLite/MySQL 一致的行为
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        return doc

    # ==========================================================
    #  用户相关
    # ==========================================================

    def create_user(self, username: str, password_hash: str, salt: str) -> int:
        user_id = self._next_id("users")
        self._users.insert_one(
            {
                "id": user_id,
                "username": username,
                "password_hash": password_hash,
                "salt": salt,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return user_id

    def get_user(self, username: str) -> RowDict | None:
        doc = self._users.find_one({"username": username})
        return self._clean_doc(doc)

    # ==========================================================
    #  密码条目相关
    # ==========================================================

    def add_password(
        self,
        user_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> int:
        entry_id = self._next_id("passwords")
        now = datetime.now(timezone.utc)
        self._passwords.insert_one(
            {
                "id": entry_id,
                "user_id": user_id,
                "site_name": site_name,
                "url": url,
                "account": account,
                "password": password,
                "notes": notes,
                "created_at": now,
                "updated_at": now,
            }
        )
        return entry_id

    def get_passwords(self, user_id: int) -> list[RowDict]:
        cursor = self._passwords.find(
            {"user_id": user_id}
        ).sort("site_name", ASCENDING)
        return [self._clean_doc(doc) for doc in cursor]

    def update_password(
        self,
        entry_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> None:
        self._passwords.update_one(
            {"id": entry_id},
            {
                "$set": {
                    "site_name": site_name,
                    "url": url,
                    "account": account,
                    "password": password,
                    "notes": notes,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    def delete_password(self, entry_id: int) -> None:
        self._passwords.delete_one({"id": entry_id})
