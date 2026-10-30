# -*- coding: utf-8 -*-
"""知识溯源数据初始化（幂等）：建表 + 种子数据。"""
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
import pymysql  # noqa: E402


def main() -> None:
    sql = (BACKEND.parent / "sql" / "traces.sql").read_text(encoding="utf-8")
    # 去掉注释行，按分号切分语句
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    stmts = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        autocommit=True,
    )
    cur = conn.cursor()
    for stmt in stmts:
        cur.execute(stmt)
    cur.execute("SELECT COUNT(*) FROM kb_trace")
    traces = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM kb_trace_node")
    nodes = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"[ok] kb_trace = {traces} 条，kb_trace_node = {nodes} 条")


if __name__ == "__main__":
    main()
