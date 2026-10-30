"""知识管理模块初始化：补齐 kb_entry 扩展字段 + 执行 sql/knowledge.sql 种子数据。

幂等：字段/索引按 information_schema 检测后按需 ALTER；种子数据由 SQL 内的
INSERT ... WHERE NOT EXISTS 保证不重复。可重复运行。
"""
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "knowledge.sql"

# 知识管理依赖的 kb_entry 扩展字段（字段名 -> ALTER 子句）
EXTRA_COLUMNS: dict[str, str] = {
    "knowledge_type": "ADD COLUMN `knowledge_type` VARCHAR(30) NOT NULL DEFAULT '' COMMENT '知识类型' AFTER `summary`",
    "source_dept": "ADD COLUMN `source_dept` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '来源部门' AFTER `knowledge_type`",
    "keywords": "ADD COLUMN `keywords` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '关键词(英文逗号分隔)' AFTER `source_dept`",
    "status": "ADD COLUMN `status` TINYINT NOT NULL DEFAULT 1 COMMENT '0=草稿 1=已发布 2=已下线' AFTER `keywords`",
    "publish_at": "ADD COLUMN `publish_at` DATETIME NULL COMMENT '发布时间' AFTER `status`",
}

EXTRA_INDEXES: dict[str, str] = {
    "idx_entry_status": "ADD KEY `idx_entry_status` (`status`)",
    "idx_entry_ktype": "ADD KEY `idx_entry_ktype` (`knowledge_type`)",
}


def connect():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
        connect_timeout=10,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def ensure_schema(conn, table: str) -> list[str]:
    changed: list[str] = []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
            (settings.DB_NAME, table),
        )
        cols = {r[0] for r in cur.fetchall()}
        for name, clause in EXTRA_COLUMNS.items():
            if name not in cols:
                cur.execute(f"ALTER TABLE `{table}` {clause}")
                changed.append(f"column {name}")

        cur.execute(f"SHOW INDEX FROM `{table}`")
        idx = {r[2] for r in cur.fetchall()}
        for name, clause in EXTRA_INDEXES.items():
            if name not in idx:
                cur.execute(f"ALTER TABLE `{table}` {clause}")
                changed.append(f"index {name}")
    conn.commit()
    return changed


def main() -> int:
    conn = connect()
    try:
        changed = ensure_schema(conn, "kb_entry")
        print("SCHEMA:", ", ".join(changed) if changed else "已是最新，无需变更")

        sql = SQL_FILE.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            while cur.nextset():
                pass
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM kb_category WHERE is_deleted = 0")
            print("categories:", cur.fetchone()[0])
            cur.execute(
                "SELECT id, name, level, path FROM kb_category "
                "WHERE is_deleted = 0 AND name IN "
                "('政务服务事项','政策法规','高效办成一件事','办事指南','常见问答','数据标准规范')"
            )
            for row in cur.fetchall():
                print("CATEGORY:", row)

            cur.execute(
                "SELECT status, COUNT(*) FROM kb_entry WHERE is_deleted = 0 GROUP BY status"
            )
            print("entries_by_status:", cur.fetchall())
            cur.execute(
                "SELECT knowledge_type, COUNT(*) FROM kb_entry "
                "WHERE is_deleted = 0 GROUP BY knowledge_type"
            )
            for row in cur.fetchall():
                print("TYPE:", row)
            cur.execute(
                "SELECT COUNT(*) FROM kb_entry WHERE is_deleted = 0 AND knowledge_type <> '事项知识'"
            )
            print("seeded_knowledge:", cur.fetchone()[0])
            cur.execute(
                "SELECT COUNT(*) FROM kb_entry_tag et JOIN kb_entry e ON e.id = et.entry_id "
                "WHERE e.is_deleted = 0"
            )
            print("entry_tag_links:", cur.fetchone()[0])
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"KNOWLEDGE_SQL_FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
