"""
database.py - 数据库统一接口层
保持原有函数签名不变，内部委托给可配置的数据库后端。
可选集成 Redis 缓存层，加速热数据读取。

外部模块（auth_view, main_view 等）只需 import database as db，
调用方式完全不变：db.init_db(), db.get_user(), db.add_password() ...

通过修改项目根目录的 db_config.json 即可切换数据库类型，无需改动任何业务代码。
Redis 缓存为可选功能，不可用时自动降级为纯数据库模式。
"""

from typing import Any

from db_config import create_backend, load_config
from db_backend import DatabaseBackend

# 全局后端实例（延迟初始化）
_backend: DatabaseBackend | None = None

# 全局 Redis 缓存实例（可选，可能为 None）
_cache = None


def _get_backend() -> DatabaseBackend:
    """获取当前数据库后端实例，首次调用时自动创建"""
    global _backend
    if _backend is None:
        _backend = create_backend()
    return _backend


def _get_cache():
    """获取 Redis 缓存实例，不可用时返回 None（静默降级）"""
    global _cache
    # 已经尝试过初始化（成功或失败），直接返回
    if _cache is not False:
        return _cache
    return None


def _init_cache() -> None:
    """尝试初始化 Redis 缓存，失败则标记为不可用"""
    global _cache
    try:
        config = load_config()
        redis_conf = config.get("redis")
        if redis_conf is None or not redis_conf.get("enabled", False):
            _cache = None
            return

        from redis_cache import RedisCache

        _cache = RedisCache(
            host=redis_conf.get("host", "127.0.0.1"),
            port=redis_conf.get("port", 6379),
            db=redis_conf.get("db", 0),
            password=redis_conf.get("password") or None,
            default_ttl=redis_conf.get("default_ttl", 300),
        )
        if not _cache.ping():
            print("[缓存] Redis 连接失败，将以纯数据库模式运行")
            _cache = None
        else:
            print("[缓存] Redis 缓存层已启用")
    except Exception as e:
        print(f"[缓存] Redis 初始化失败（{e}），将以纯数据库模式运行")
        _cache = None


# ---------- 生命周期 ----------


def init_db() -> None:
    """初始化数据库，创建所需的表；同时尝试初始化 Redis 缓存"""
    _get_backend().init_db()
    _init_cache()


def close_db() -> None:
    """关闭数据库连接/释放资源"""
    global _backend, _cache
    if _backend is not None:
        _backend.close()
        _backend = None
    if _cache is not None:
        _cache.close()
        _cache = None


# ---------- 用户相关 ----------


def create_user(username: str, password_hash: str, salt: str) -> int:
    """新建用户，返回 user_id"""
    user_id = _get_backend().create_user(username, password_hash, salt)
    # 新建用户后无需缓存，等查询时再缓存
    return user_id


def get_user(username: str) -> dict[str, Any] | None:
    """按用户名查询用户，返回字典或 None（优先读缓存）"""
    cache = _get_cache()

    # 尝试从缓存读取
    if cache is not None:
        cached = cache.get_cached_user(username)
        if cached is not None:
            return cached

    # 缓存未命中，查数据库
    user = _get_backend().get_user(username)

    # 回填缓存
    if user is not None and cache is not None:
        cache.cache_user(username, user)

    return user


def username_exists(username: str) -> bool:
    """判断用户名是否已存在"""
    return _get_backend().username_exists(username)


# ---------- 密码条目相关 ----------


def add_password(
    user_id: int, site_name: str, url: str, account: str, password: str, notes: str
) -> int:
    """添加密码条目，返回条目 id"""
    entry_id = _get_backend().add_password(
        user_id, site_name, url, account, password, notes)
    # 数据变更，失效缓存
    cache = _get_cache()
    if cache is not None:
        cache.invalidate_passwords(user_id)
    return entry_id


def get_passwords(user_id: int) -> list[dict[str, Any]]:
    """获取用户所有密码条目（优先读缓存）"""
    cache = _get_cache()

    # 尝试从缓存读取
    if cache is not None:
        cached = cache.get_cached_passwords(user_id)
        if cached is not None:
            return cached

    # 缓存未命中，查数据库
    passwords = _get_backend().get_passwords(user_id)

    # 回填缓存
    if cache is not None:
        cache.cache_passwords(user_id, passwords)

    return passwords


def update_password(
    entry_id: int, site_name: str, url: str, account: str, password: str, notes: str,
    user_id: int | None = None,
) -> None:
    """更新密码条目"""
    _get_backend().update_password(entry_id, site_name, url, account, password, notes)
    # 数据变更，失效缓存
    cache = _get_cache()
    if cache is not None and user_id is not None:
        cache.invalidate_passwords(user_id)


def delete_password(entry_id: int, user_id: int | None = None) -> None:
    """删除密码条目"""
    _get_backend().delete_password(entry_id)
    # 数据变更，失效缓存
    cache = _get_cache()
    if cache is not None and user_id is not None:
        cache.invalidate_passwords(user_id)


# ---------- Redis 缓存直接访问（供业务层按需使用） ----------


def get_cache():
    """获取 Redis 缓存实例，供业务层直接使用（如会话管理、登录限制等）。
    未启用 Redis 时返回 None。
    """
    return _get_cache()
