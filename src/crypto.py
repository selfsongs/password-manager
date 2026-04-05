"""
crypto.py - 加密模块
- bcrypt 负责主密码哈希验证
- PBKDF2 + AES (Fernet) 负责加解密存储的密码条目
"""

from db_backend import DatabaseBackend
from db_config import create_backend
from typing import Any
import os
import base64
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def generate_salt() -> str:
    """生成随机 salt（用于派生加密密钥），返回 base64 字符串"""
    return base64.b64encode(os.urandom(32)).decode()


def hash_password(password: str) -> str:
    """用 bcrypt 哈希主密码"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """校验主密码"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _derive_key(master_password: str, salt: str) -> Fernet:
    """从主密码 + salt 派生 Fernet 对称密钥"""
    salt_bytes = base64.b64decode(salt.encode())
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt_bytes,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return Fernet(key)


def encrypt(plaintext: str, master_password: str, salt: str) -> str:
    """加密明文字符串，返回 base64 密文"""
    f = _derive_key(master_password, salt)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, master_password: str, salt: str) -> str:
    """解密密文，返回明文字符串"""
    f = _derive_key(master_password, salt)
    return f.decrypt(ciphertext.encode()).decode()


"""
database.py - 数据库统一接口层
保持原有函数签名不变，内部委托给可配置的数据库后端。

外部模块（auth_view, main_view 等）只需 import database as db，
调用方式完全不变：db.init_db(), db.get_user(), db.add_password() ...

通过修改项目根目录的 db_config.json 即可切换数据库类型，无需改动任何业务代码。
"""


# 全局后端实例（延迟初始化）
_backend: DatabaseBackend | None = None


def _get_backend() -> DatabaseBackend:
    """获取当前数据库后端实例，首次调用时自动创建"""
    global _backend
    if _backend is None:
        _backend = create_backend()
    return _backend


# ---------- 生命周期 ----------


def init_db() -> None:
    """初始化数据库，创建所需的表"""
    _get_backend().init_db()


def close_db() -> None:
    """关闭数据库连接/释放资源"""
    global _backend
    if _backend is not None:
        _backend.close()
        _backend = None


# ---------- 用户相关 ----------


def create_user(username: str, password_hash: str, salt: str) -> int:
    """新建用户，返回 user_id"""
    return _get_backend().create_user(username, password_hash, salt)


def get_user(username: str) -> dict[str, Any] | None:
    """按用户名查询用户，返回字典或 None"""
    return _get_backend().get_user(username)


def username_exists(username: str) -> bool:
    """判断用户名是否已存在"""
    return _get_backend().username_exists(username)


# ---------- 密码条目相关 ----------


def add_password(
    user_id: int, site_name: str, url: str, account: str, password: str, notes: str
) -> int:
    """添加密码条目，返回条目 id"""
    return _get_backend().add_password(user_id, site_name, url, account, password, notes)


def get_passwords(user_id: int) -> list[dict[str, Any]]:
    """获取用户所有密码条目（搜索过滤已移至应用层，因 account 为加密字段无法在 SQL 中匹配）"""
    return _get_backend().get_passwords(user_id)


def update_password(
    entry_id: int, site_name: str, url: str, account: str, password: str, notes: str
) -> None:
    """更新密码条目"""
    _get_backend().update_password(entry_id, site_name, url, account, password, notes)


def delete_password(entry_id: int) -> None:
    """删除密码条目"""
    _get_backend().delete_password(entry_id)
