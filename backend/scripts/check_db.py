"""Stage-1 acceptance: connectivity, server facts, table inventory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymysql
import sqlalchemy

from app.core.config import settings


def main() -> int:
    print(f"sqlalchemy={sqlalchemy.__version__}")
    print(f"target={settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} user={settings.DB_USER}")

    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
        connect_timeout=10,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT VERSION(), CURRENT_USER(), DATABASE(), "
                "@@character_set_server, @@collation_server, @@time_zone, @@default_storage_engine"
            )
            row = cur.fetchone()
            keys = [
                "version", "current_user", "database",
                "character_set_server", "collation_server", "time_zone", "storage_engine",
            ]
            print({k: v for k, v in zip(keys, row)})

            cur.execute("SHOW GRANTS FOR CURRENT_USER()")
            for (grant,) in cur.fetchall():
                print("GRANT:", grant)

            cur.execute("SHOW TABLES")
            tables = [t for (t,) in cur.fetchall()]
            print(f"tables ({len(tables)}):", tables)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"CONNECT_FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
