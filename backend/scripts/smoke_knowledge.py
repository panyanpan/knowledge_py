"""知识管理模块 HTTP 冒烟：直接用 DB 用户签发 token（不在命令行暴露口令）。"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_token_pair
from app.models.user import SysUser

BASE = "http://127.0.0.1:8000"
PASSED = []
FAILED = []


def token_for(username: str) -> str:
    db = SessionLocal()
    try:
        user = db.scalar(select(SysUser).where(SysUser.username == username))
        assert user is not None, f"user {username} not found"
        return create_token_pair(user_id=user.id, token_version=user.token_version)["access_token"]
    finally:
        db.close()


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(name)
    print(f"{'PASS' if cond else 'FAIL'} | {name} {detail}")


def main() -> int:
    admin = token_for("admin")
    user = token_for("tester01")

    st, r = call("GET", "/api/v1/knowledge/options", admin)
    d = r.get("data") or {}
    check(
        "选项接口(类型/状态/分类)",
        st == 200 and len(d.get("knowledge_types", [])) == 6 and d.get("categories"),
        f"types={d.get('knowledge_types')} cats={len(d.get('categories', []))}",
    )

    st, r = call("GET", "/api/v1/knowledge/stats", admin)
    d = r.get("data") or {}
    check(
        "统计接口",
        st == 200 and d.get("total", 0) >= 20 and d.get("published", 0) >= 18,
        f"total={d.get('total')} published={d.get('published')} draft={d.get('draft')} month={d.get('month_new')}",
    )
    check("统计按类型分组", st == 200 and len(d.get("by_type", {})) >= 5, str(d.get("by_type")))

    st, r = call("GET", "/api/v1/knowledge?page=1&page_size=10", admin)
    page = r.get("data") or {}
    check(
        "清单分页",
        st == 200 and page.get("total", 0) >= 20 and len(page.get("list", [])) == 10,
        f"total={page.get('total')} size={len(page.get('list', []))}",
    )
    first = (page.get("list") or [{}])[0]
    check(
        "列表项含分类名/状态文案/更新时间",
        bool(first.get("category_name")) and first.get("status_label") in ("草稿", "已发布", "已下线"),
        f"{first.get('title')} | {first.get('category_name')} | {first.get('status_label')}",
    )

    q = urllib.parse.quote("事项知识")
    st, r = call("GET", f"/api/v1/knowledge?knowledge_type={q}&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("类型筛选(事项知识)", st == 200 and rows and all(x["knowledge_type"] == "事项知识" for x in rows), f"count={len(rows)}")

    cats = (call("GET", "/api/v1/knowledge/options", admin)[1].get("data") or {}).get("categories", [])
    item_cat = next((c["id"] for c in cats if c["name"] == "政务服务事项"), None)
    st, r = call("GET", f"/api/v1/knowledge?category_id={item_cat}&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("分类筛选(政务服务事项)", st == 200 and rows and all(x["category_id"] == item_cat for x in rows), f"count={len(rows)}")

    st, r = call("GET", "/api/v1/knowledge?keyword=%E4%B8%80%E4%BB%B6%E4%BA%8B&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("关键词搜索(一件事)", st == 200 and len(rows) >= 4, f"count={len(rows)}")

    st, r = call("GET", "/api/v1/knowledge?status=0&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("状态筛选(草稿)", st == 200 and rows and all(x["status"] == 0 for x in rows), f"count={len(rows)}")

    st, r = call("GET", "/api/v1/knowledge?page_size=1", admin)
    kid = ((r.get("data") or {}).get("list") or [{}])[0].get("id")
    st, r = call("GET", f"/api/v1/knowledge/{kid}", admin)
    d = r.get("data") or {}
    check("详情含正文", st == 200 and bool(d.get("content")), f"id={kid} content_len={len(d.get('content') or '')}")

    st, r = call("GET", "/api/v1/knowledge/999999", admin)
    check("详情 404", st == 404 and r.get("code") == 2501, f"http={st} code={r.get('code')}")

    payload = {
        "title": "冒烟测试知识条目",
        "category_id": ((call("GET", "/api/v1/knowledge/options", admin)[1].get("data") or {}).get("categories") or [{}])[0].get("id"),
        "knowledge_type": "事项知识",
        "summary": "冒烟测试用",
        "content": "<p>正文<script>alert(1)</script></p>",
        "source_dept": "省政务服务中心",
        "keywords": "冒烟,测试",
        "status": 1,
    }
    st, r = call("POST", "/api/v1/knowledge", admin, payload)
    new_id = (r.get("data") or {}).get("id")
    saved = (r.get("data") or {}).get("content") or ""
    check("新增知识(201)", st == 201 and new_id, f"id={new_id} code={r.get('code')}")
    check("富文本入库前清洗(script 被剥离)", "script" not in saved.lower(), saved[:60])

    st, r = call("PUT", f"/api/v1/knowledge/{new_id}", admin, {"title": "冒烟测试知识条目-改", "keywords": "冒烟,改"})
    check("编辑知识", st == 200 and r["data"]["title"].endswith("-改"), "")

    st, r = call("POST", f"/api/v1/knowledge/{new_id}/status?status=0", admin)
    check("下架为草稿", st == 200 and r["data"]["status"] == 0 and r["data"]["status_label"] == "草稿", "")

    st, r = call("POST", f"/api/v1/knowledge/{new_id}/status?status=9", admin)
    check("非法状态拦截(422)", st == 422, f"http={st}")

    st, r = call("PUT", f"/api/v1/knowledge/{kid}", user, {"title": "越权改名"})
    check("USER 越权编辑被拒(403)", st == 403 and r.get("code") == 2502, f"http={st} code={r.get('code')}")

    st, r = call("GET", "/api/v1/knowledge/export", admin)
    ok_csv = st == 200 and isinstance(r, str) and r.startswith("\ufeff") and "知识标题" in r
    check("CSV 导出(含 BOM+表头)", ok_csv, f"http={st}")

    st, r = call("DELETE", f"/api/v1/knowledge/{new_id}", admin)
    st2, r2 = call("GET", f"/api/v1/knowledge/{new_id}", admin)
    check("删除知识(软删后 404)", st == 200 and st2 == 404, f"get_after_delete={st2}")

    print(f"\nRESULT: {len(PASSED)} passed, {len(FAILED)} failed")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
