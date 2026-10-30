"""Execute sql/schema.sql against the configured database (multi-statement)."""
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

SCHEMA = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


def main() -> int:
    sql = SCHEMA.read_text(encoding="utf-8")
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
        connect_timeout=10,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            while cur.nextset():
                pass
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            tables = [t for (t,) in cur.fetchall()]
            print(f"TABLES_CREATED ({len(tables)}):", tables)
            cur.execute("SELECT id, username, email, role_id, status, LEFT(password_hash, 7) FROM sys_user")
            for row in cur.fetchall():
                print("USER:", row)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"SCHEMA_FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
