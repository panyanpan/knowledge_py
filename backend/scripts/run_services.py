"""幂等执行 sql/services.sql：建 kb_service 表 + 灌入服务演示数据。"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
import pymysql  # noqa: E402


def main() -> None:
    sql_path = BACKEND_DIR.parent / "sql" / "services.sql"
    sql = sql_path.read_text(encoding="utf-8")

    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
                lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith("--")]
                body = "\n".join(lines).strip()
                if not body:
                    continue
                cur.execute(body)
            cur.execute("SELECT COUNT(*) FROM kb_service")
            total = cur.fetchone()[0]
            cur.execute("SELECT svc_code, svc_name, svc_type, status FROM kb_service ORDER BY sort_order DESC")
            rows = cur.fetchall()
        print(f"kb_service 共 {total} 项服务：")
        for code, name, stype, status in rows:
            print(f"  {code}  {name}  [{stype}]  status={status}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
