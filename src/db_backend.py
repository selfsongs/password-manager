"""
db_backend.py - 数据库后端抽象基类
定义所有数据库操作的统一接口，具体实现由各后端子类提供。
"""

from abc import ABC, abstractmethod
from typing import Any


# 统一的行数据类型：字典形式，支持 row["field"] 访问
RowDict = dict[str, Any]


class DatabaseBackend(ABC):
    """数据库后端抽象基类"""

    @abstractmethod
    def init_db(self) -> None:
        """初始化数据库，创建所需的表"""
        ...

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接/释放资源"""
        ...

    # ---------- 用户相关 ----------

    @abstractmethod
    def create_user(self, username: str, password_hash: str, salt: str) -> int:
        """新建用户，返回 user_id"""
        ...

    @abstractmethod
    def get_user(self, username: str) -> RowDict | None:
        """按用户名查询用户，返回字典或 None"""
        ...

    def username_exists(self, username: str) -> bool:
        """判断用户名是否已存在"""
        return self.get_user(username) is not None

    # ---------- 密码条目相关 ----------

    @abstractmethod
    def add_password(
        self,
        user_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> int:
        """添加密码条目，返回条目 id"""
        ...

    @abstractmethod
    def get_passwords(self, user_id: int) -> list[RowDict]:
        """获取用户所有密码条目"""
        ...

    @abstractmethod
    def update_password(
        self,
        entry_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> None:
        """更新密码条目"""
        ...

    @abstractmethod
    def delete_password(self, entry_id: int) -> None:
        """删除密码条目"""
        ...
