"""
redis_cache.py - Redis 缓存层
作为数据库后端的辅助缓存，加速热数据读取，提供会话管理与安全防护能力。
需要安装依赖：pip install redis
"""

from __future__ import annotations

import json
from typing import Any

try:
    import redis
except ImportError:
    redis = None  # type: ignore


# 统一的行数据类型
RowDict = dict[str, Any]


class RedisCache:
    """Redis 缓存层 —— 配合 DatabaseBackend 使用，而非替代它。

    职责：
      1. 密码条目列表缓存（减少数据库查询）
      2. 用户信息缓存
      3. 登录会话管理（Token → user_id，支持过期）
      4. 登录失败计数（防暴力破解）
      5. 数据变更时主动失效缓存
    """

    # ---------- Key 命名前缀 ----------
    PREFIX_PASSWORDS = "cache:passwords:"      # + user_id
    PREFIX_USER = "cache:user:"                # + username
    PREFIX_SESSION = "session:"                # + token
    PREFIX_LOGIN_FAIL = "login_fail:"          # + username

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        default_ttl: int = 300,
    ):
        """
        Args:
            host: Redis 服务器地址
            port: Redis 端口
            db: Redis 数据库编号（0-15）
            password: Redis 密码，无密码时为 None
            default_ttl: 默认缓存过期时间（秒），默认 5 分钟
        """
        if redis is None:
            raise ImportError(
                "Redis 缓存层需要 redis 库，请运行：pip install redis"
            )
        self._client: redis.Redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,  # 自动将 bytes 解码为 str
        )
        self.default_ttl = default_ttl

    # ==========================================================
    #  连接检测
    # ==========================================================

    def ping(self) -> bool:
        """检测 Redis 连接是否正常"""
        try:
            return self._client.ping()
        except Exception:
            return False

    def close(self) -> None:
        """关闭 Redis 连接"""
        self._client.close()

    # ==========================================================
    #  1. 密码条目缓存
    # ==========================================================

    def cache_passwords(
        self, user_id: int, data: list[RowDict], ttl: int | None = None
    ) -> None:
        """缓存用户的密码条目列表。

        Args:
            user_id: 用户 ID
            data: 密码条目列表（字典列表）
            ttl: 过期时间（秒），默认使用 default_ttl
        """
        key = f"{self.PREFIX_PASSWORDS}{user_id}"
        # 将列表序列化为 JSON 存储
        self._client.set(key, json.dumps(
            data, ensure_ascii=False, default=str))
        self._client.expire(key, ttl or self.default_ttl)

    def get_cached_passwords(self, user_id: int) -> list[RowDict] | None:
        """获取缓存的密码条目列表。

        Returns:
            命中时返回字典列表，未命中返回 None（调用方应回源查数据库）。
        """
        key = f"{self.PREFIX_PASSWORDS}{user_id}"
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def invalidate_passwords(self, user_id: int) -> None:
        """使指定用户的密码条目缓存失效（数据变更时调用）。"""
        self._client.delete(f"{self.PREFIX_PASSWORDS}{user_id}")

    # ==========================================================
    #  2. 用户信息缓存
    # ==========================================================

    def cache_user(
        self, username: str, user_data: RowDict, ttl: int | None = None
    ) -> None:
        """缓存用户信息。"""
        key = f"{self.PREFIX_USER}{username}"
        self._client.set(
            key, json.dumps(user_data, ensure_ascii=False, default=str)
        )
        self._client.expire(key, ttl or self.default_ttl)

    def get_cached_user(self, username: str) -> RowDict | None:
        """获取缓存的用户信息，未命中返回 None。"""
        key = f"{self.PREFIX_USER}{username}"
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def invalidate_user(self, username: str) -> None:
        """使用户信息缓存失效。"""
        self._client.delete(f"{self.PREFIX_USER}{username}")

    # ==========================================================
    #  3. 登录会话管理
    # ==========================================================

    def set_session(
        self, token: str, user_id: int, ttl: int = 3600
    ) -> None:
        """保存登录会话。

        Args:
            token: 会话令牌（如 UUID）
            user_id: 关联的用户 ID
            ttl: 会话有效期（秒），默认 1 小时
        """
        key = f"{self.PREFIX_SESSION}{token}"
        self._client.set(key, str(user_id))
        self._client.expire(key, ttl)

    def get_session(self, token: str) -> int | None:
        """根据令牌获取 user_id，会话过期或不存在时返回 None。"""
        key = f"{self.PREFIX_SESSION}{token}"
        val = self._client.get(key)
        return int(val) if val is not None else None

    def refresh_session(self, token: str, ttl: int = 3600) -> bool:
        """刷新会话过期时间（续期），返回是否成功。"""
        key = f"{self.PREFIX_SESSION}{token}"
        return bool(self._client.expire(key, ttl))

    def delete_session(self, token: str) -> None:
        """删除会话（登出时调用）。"""
        self._client.delete(f"{self.PREFIX_SESSION}{token}")

    # ==========================================================
    #  4. 登录失败计数（防暴力破解）
    # ==========================================================

    def incr_login_fail(
        self, username: str, window: int = 900
    ) -> int:
        """登录失败次数 +1，返回当前累计次数。

        Args:
            username: 用户名
            window: 计数窗口期（秒），默认 15 分钟

        Returns:
            窗口期内的累计失败次数
        """
        key = f"{self.PREFIX_LOGIN_FAIL}{username}"
        count = self._client.incr(key)
        # 首次设置时添加过期时间
        if count == 1:
            self._client.expire(key, window)
        return count

    def get_login_fail_count(self, username: str) -> int:
        """获取当前失败次数。"""
        key = f"{self.PREFIX_LOGIN_FAIL}{username}"
        val = self._client.get(key)
        return int(val) if val is not None else 0

    def reset_login_fail(self, username: str) -> None:
        """登录成功后重置失败计数。"""
        self._client.delete(f"{self.PREFIX_LOGIN_FAIL}{username}")

    def is_locked_out(self, username: str, max_attempts: int = 5) -> bool:
        """判断用户是否因失败次数过多被锁定。"""
        return self.get_login_fail_count(username) >= max_attempts
