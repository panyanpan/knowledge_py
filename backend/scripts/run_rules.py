"""幂等执行 sql/rules.sql：建 kb_rule 表 + 灌入规则种子数据。"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
import pymysql  # noqa: E402


def main() -> None:
    sql_path = BACKEND_DIR.parent / "sql" / "rules.sql"
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
                # 去掉行内注释行后执行
                lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith("--")]
                body = "\n".join(lines).strip()
                if not body:
                    continue
                cur.execute(body)
            cur.execute("SELECT COUNT(*) FROM kb_rule")
            total = cur.fetchone()[0]
            cur.execute("SELECT rule_code, rule_name, rule_type, status FROM kb_rule ORDER BY sort_order DESC, id ASC")
            rows = cur.fetchall()
        print(f"kb_rule 共 {total} 条规则：")
        for code, name, rtype, status in rows:
            print(f"  {code}  {name}  [{rtype}]  status={status}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
