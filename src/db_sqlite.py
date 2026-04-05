"""
db_sqlite.py - SQLite 数据库后端实现
"""

import os
import sqlite3
from pathlib import Path

from db_backend import DatabaseBackend, RowDict


class SQLiteBackend(DatabaseBackend):
    """SQLite 数据库后端"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent /
                          "data" / "passwords.db")
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> RowDict | None:
        """将 sqlite3.Row 转换为普通字典"""
        if row is None:
            return None
        return dict(row)

    @staticmethod
    def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[RowDict]:
        """将 sqlite3.Row 列表转换为字典列表"""
        return [dict(r) for r in rows]

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt          TEXT NOT NULL,
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS passwords (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    site_name     TEXT NOT NULL,
                    url           TEXT,
                    account       TEXT NOT NULL,
                    password      TEXT NOT NULL,
                    notes         TEXT,
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def close(self) -> None:
        # SQLite 使用短连接模式，无需显式关闭
        pass

    # ---------- 用户相关 ----------

    def create_user(self, username: str, password_hash: str, salt: str) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, password_hash, salt),
            )
            return cur.lastrowid or 0

    def get_user(self, username: str) -> RowDict | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return self._row_to_dict(row)

    # ---------- 密码条目相关 ----------

    def add_password(
        self,
        user_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO passwords (user_id, site_name, url, account, password, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, site_name, url, account, password, notes),
            )
            return cur.lastrowid or 0

    def get_passwords(self, user_id: int) -> list[RowDict]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM passwords WHERE user_id = ? ORDER BY site_name",
                (user_id,),
            ).fetchall()
            return self._rows_to_dicts(rows)

    def update_password(
        self,
        entry_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE passwords
                   SET site_name=?, url=?, account=?, password=?, notes=?,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (site_name, url, account, password, notes, entry_id),
            )

    def delete_password(self, entry_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM passwords WHERE id=?", (entry_id,))
