# -*- coding: utf-8 -*-
"""知识溯源接口冒烟测试。"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.database import SessionLocal  # noqa: E402
from app.core.security import create_token_pair  # noqa: E402
from app.models.user import SysUser  # noqa: E402
from sqlalchemy import select  # noqa: E402

BASE = "http://127.0.0.1:8000"
passed = failed = 0


def token_for(username: str) -> str:
    db = SessionLocal()
    try:
        u = db.scalar(select(SysUser).where(SysUser.username == username))
        return create_token_pair(user_id=u.id, token_version=u.token_version)["access_token"]
    finally:
        db.close()


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    req = urllib.request.Request(BASE + path, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name: str, cond: bool, extra: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"[PASS] {name} {extra}")
    else:
        failed += 1
        print(f"[FAIL] {name} {extra}")


def main():
    admin = token_for("admin")

    # 1. 统计
    st, r = call("GET", "/api/v1/traces/stats", admin)
    d = r.get("data") or {}
    check("统计接口", st == 200 and d.get("chain_complete") == 3 and d.get("chain_missing") == 1,
          f"stats={d}")

    # 2. 快捷选项
    st, r = call("GET", "/api/v1/traces/options", admin)
    chips = (r.get("data") or {}).get("chips", [])
    check("快捷主题4个", st == 200 and len(chips) == 4, f"chips={[c['title'] for c in chips]}")

    # 3. 列表
    st, r = call("GET", "/api/v1/traces", admin)
    check("列表", st == 200 and r.get("data", {}).get("total") == 4)

    # 4. 关键词检索（主题）
    q = urllib.parse.quote("企业上市")
    st, r = call("GET", f"/api/v1/traces?keyword={q}", admin)
    rows = r.get("data", {}).get("list", [])
    check("关键词检索-主题", st == 200 and len(rows) == 1 and rows[0]["trace_no"] == "TR-2026-002")

    # 5. 关键词检索（知识编号）
    q = urllib.parse.quote("KB-MZ-2026-000338")
    st, r = call("GET", f"/api/v1/traces?keyword={q}", admin)
    rows = r.get("data", {}).get("list", [])
    check("关键词检索-编号", st == 200 and len(rows) == 1 and rows[0]["scene"] == "社会救助综合受理")

    # 6. 无关键词不误命中
    st, r = call("GET", "/api/v1/traces", admin)
    check("列表含场景字段", all("scene" in x for x in r["data"]["list"]))

    # 7. 详情（含6环节+凭证）
    tid = chips[0]["id"]
    st, r = call("GET", f"/api/v1/traces/{tid}", admin)
    d = r.get("data") or {}
    nodes = d.get("nodes", [])
    check("详情6环节", st == 200 and len(nodes) == 6, f"nodes={[n['name'] for n in nodes]}")
    check("环节含凭证", all(n.get("evidence") for n in nodes))
    check("环节升序", [n["step_no"] for n in nodes] == [1, 2, 3, 4, 5, 6])

    # 8. 溯源查询留痕
    before = d["query_count"]
    st, r = call("POST", f"/api/v1/traces/{tid}/run", admin)
    d2 = (r.get("data") or {})
    check("溯源run留痕", st == 200 and d2.get("query_count") == before + 1 and len(d2.get("nodes", [])) == 6,
          f"query_count {before} -> {d2.get('query_count')}")

    # 9. 详情不存在
    st, r = call("GET", "/api/v1/traces/99999", admin)
    check("404业务码2801", st == 404 and r.get("code") == 2801)

    # 10. 未登录被拒
    st, r = call("GET", "/api/v1/traces/stats")
    check("未登录401", st == 401)

    # 11. 缺失链路主题返回 chain_status=0
    q = urllib.parse.quote("社会救助")
    st, r = call("GET", f"/api/v1/traces?keyword={q}", admin)
    check("缺失链路标记", st == 200 and r["data"]["list"][0]["chain_status"] == 0)

    # 12. 溯源主题run后 last_query_at 更新
    st, r = call("GET", f"/api/v1/traces/{tid}", admin)
    check("最近溯源时间更新", st == 200 and r["data"]["last_query_at"])

    print(f"\n==== 冒烟结果：{passed} 通过 / {failed} 失败 ====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import urllib.parse  # noqa: F401
    main()
