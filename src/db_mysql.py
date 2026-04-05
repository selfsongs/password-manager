"""
db_mysql.py - MySQL 数据库后端实现
需要安装依赖：pip install pymysql
"""

from db_backend import DatabaseBackend, RowDict

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None  # type: ignore


class MySQLBackend(DatabaseBackend):
    """MySQL 数据库后端"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "password_manager",
        charset: str = "utf8mb4",
    ):
        if pymysql is None:
            raise ImportError(
                "MySQL 后端需要 pymysql 库，请运行：pip install pymysql"
            )
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": charset,
            "cursorclass": pymysql.cursors.DictCursor,  # 返回字典格式
        }
        self._ensure_database(host, port, user, password, database, charset)

    def _ensure_database(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        charset: str,
    ) -> None:
        """确保目标数据库存在，不存在则自动创建"""
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset=charset,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    f"DEFAULT CHARACTER SET {charset} COLLATE {charset}_unicode_ci"
                )
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> "pymysql.connections.Connection":
        conn = pymysql.connect(**self.conn_params)
        return conn

    def init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        username      VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        salt          VARCHAR(255) NOT NULL,
                        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS passwords (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        user_id       INT NOT NULL,
                        site_name     VARCHAR(255) NOT NULL,
                        url           TEXT,
                        account       TEXT NOT NULL,
                        password      TEXT NOT NULL,
                        notes         TEXT,
                        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        # 使用短连接模式，无需额外关闭
        pass

    # ---------- 用户相关 ----------

    def create_user(self, username: str, password_hash: str, salt: str) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)",
                    (username, password_hash, salt),
                )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            conn.close()

    def get_user(self, username: str) -> RowDict | None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users WHERE username = %s", (username,)
                )
                return cur.fetchone()
        finally:
            conn.close()

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
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO passwords (user_id, site_name, url, account, password, notes)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, site_name, url, account, password, notes),
                )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            conn.close()

    def get_passwords(self, user_id: int) -> list[RowDict]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM passwords WHERE user_id = %s ORDER BY site_name",
                    (user_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    def update_password(
        self,
        entry_id: int,
        site_name: str,
        url: str,
        account: str,
        password: str,
        notes: str,
    ) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE passwords
                       SET site_name=%s, url=%s, account=%s, password=%s, notes=%s
                       WHERE id=%s""",
                    (site_name, url, account, password, notes, entry_id),
                )
            conn.commit()
        finally:
            conn.close()

    def delete_password(self, entry_id: int) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM passwords WHERE id=%s", (entry_id,))
            conn.commit()
        finally:
            conn.close()
