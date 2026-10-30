"""执行 sql/metadata.sql（建元数据字段表 + 种子数据），幂等可重复运行。"""
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "metadata.sql"


def main() -> int:
    sql = SQL_FILE.read_text(encoding="utf-8")
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
            cur.execute("SELECT COUNT(*) FROM kb_metadata_field WHERE is_deleted = 0")
            print("metadata_fields:", cur.fetchone()[0])
            cur.execute(
                "SELECT field_code, data_type, domain, is_required, status, rule_type "
                "FROM kb_metadata_field ORDER BY sort_order DESC"
            )
            for row in cur.fetchall():
                print("FIELD:", row)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"METADATA_SQL_FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
