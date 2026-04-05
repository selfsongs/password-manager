"""
db_postgresql.py - PostgreSQL 数据库后端实现
需要安装依赖：pip install psycopg2-binary
"""

from db_backend import DatabaseBackend, RowDict

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL 数据库后端"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
        database: str = "password_manager",
    ):
        if psycopg2 is None:
            raise ImportError(
                "PostgreSQL 后端需要 psycopg2 库，请运行：pip install psycopg2-binary"
            )
        self._db_name = database
        self._conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
        }
        self._ensure_database(database)

    # ==========================================================
    #  数据库自动创建
    # ==========================================================

    def _ensure_database(self, database: str) -> None:
        """确保目标数据库存在，不存在则自动创建。

        PostgreSQL 不支持 CREATE DATABASE IF NOT EXISTS，
        需要先连到默认库 postgres 检查再创建。
        """
        conn = psycopg2.connect(**self._conn_params, dbname="postgres")
        conn.autocommit = True  # CREATE DATABASE 不能在事务中执行
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
                )
                if cur.fetchone() is None:
                    # 数据库名需要用标识符引用，防止 SQL 注入
                    cur.execute(
                        f'CREATE DATABASE "{database}" ENCODING \'UTF8\''
                    )
        finally:
            conn.close()

    # ==========================================================
    #  连接管理（短连接模式，与 MySQL 后端一致）
    # ==========================================================

    def _get_connection(self):
        """获取到目标数据库的连接，返回字典游标模式的连接"""
        conn = psycopg2.connect(
            **self._conn_params,
            dbname=self._db_name,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        return conn

    # ==========================================================
    #  生命周期
    # ==========================================================

    def init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id            SERIAL PRIMARY KEY,
                        username      VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        salt          VARCHAR(255) NOT NULL,
                        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS passwords (
                        id            SERIAL PRIMARY KEY,
                        user_id       INTEGER NOT NULL,
                        site_name     VARCHAR(255) NOT NULL,
                        url           TEXT,
                        account       TEXT NOT NULL,
                        password      TEXT NOT NULL,
                        notes         TEXT,
                        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                # 创建触发器函数，用于自动更新 updated_at
                cur.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                """)
                # 创建触发器（如果不存在）
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_trigger WHERE tgname = 'trg_passwords_updated_at'
                        ) THEN
                            CREATE TRIGGER trg_passwords_updated_at
                            BEFORE UPDATE ON passwords
                            FOR EACH ROW
                            EXECUTE FUNCTION update_updated_at_column();
                        END IF;
                    END;
                    $$
                """)
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        # 使用短连接模式，无需额外关闭
        pass

    # ==========================================================
    #  用户相关
    # ==========================================================

    def create_user(self, username: str, password_hash: str, salt: str) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, salt) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (username, password_hash, salt),
                )
                row = cur.fetchone()
            conn.commit()
            return row["id"] if row else 0
        finally:
            conn.close()

    def get_user(self, username: str) -> RowDict | None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users WHERE username = %s", (username,)
                )
                row = cur.fetchone()
                # RealDictRow → 普通 dict
                return dict(row) if row else None
        finally:
            conn.close()

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
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO passwords (user_id, site_name, url, account, password, notes)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                    (user_id, site_name, url, account, password, notes),
                )
                row = cur.fetchone()
            conn.commit()
            return row["id"] if row else 0
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
                return [dict(row) for row in cur.fetchall()]
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
