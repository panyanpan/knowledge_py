"""元数据模块 HTTP 冒烟：直接用 DB 用户签发 token（不在命令行暴露口令）。"""
import json
import sys
import urllib.error
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
        with urllib.request.urlopen(req, timeout=15) as resp:
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

    st, r = call("GET", "/api/v1/metadata/stats", admin)
    d = r.get("data", {})
    check("统计接口", st == 200 and d.get("total", 0) >= 12, f"total={d.get('total')} enabled={d.get('enabled')} pending={d.get('pending')}")

    st, r = call("GET", "/api/v1/metadata/fields?domain=%E5%9F%BA%E7%A1%80&page=1&page_size=50", admin)
    rows = r.get("data", {}).get("list", [])
    check("域筛选(基础)", st == 200 and rows and all(x["domain"] == "基础" for x in rows), f"count={len(rows)}")

    st, r = call("GET", "/api/v1/metadata/fields?keyword=knowledge_title", admin)
    rows = r.get("data", {}).get("list", [])
    check("关键词搜索(编码)", st == 200 and any(x["field_code"] == "knowledge_title" for x in rows), f"count={len(rows)}")

    payload = {
        "field_name": "冒烟测试字段",
        "field_code": "smoke_field_x",
        "data_type": "string",
        "domain": "技术",
        "is_required": 1,
        "status": 1,
        "description": "冒烟用字段",
        "rule_type": "length",
        "rule_config": '{"min":2,"max":50}',
        "sort_order": 10,
    }
    st, r = call("POST", "/api/v1/metadata/fields", admin, payload)
    new_id = (r.get("data") or {}).get("id")
    check("新增字段", st == 201 and new_id, f"id={new_id} code={r.get('code')}")

    st, r = call("POST", "/api/v1/metadata/fields", admin, payload)
    check("字段编码重复拦截", st == 409 and r.get("code") == 2401, f"http={st} code={r.get('code')}")

    st, r = call("PUT", f"/api/v1/metadata/fields/{new_id}", admin, {"field_name": "冒烟测试字段-改", "status": 0})
    check("编辑字段(改名+停用)", st == 200 and r["data"]["field_name"].endswith("-改") and r["data"]["status"] == 0, "")

    st, r = call("POST", f"/api/v1/metadata/fields/{new_id}/check-rule", user)
    check("规则校验(length 合法)", st == 200 and r["data"]["passed"] is True, r["data"]["message"])

    st, r = call("PUT", f"/api/v1/metadata/fields/{new_id}", admin, {"rule_type": "regex", "rule_config": '{"pattern":"[a-"}'})
    st2, r2 = call("POST", f"/api/v1/metadata/fields/{new_id}/check-rule", user)
    check("规则校验(非法正则被发现)", st == 200 and r2["data"]["passed"] is False, r2["data"]["message"])

    st, r = call("POST", "/api/v1/metadata/fields/6/check-rule", user)
    check("规则校验(未配置规则)", st == 200 and r["data"]["passed"] is False, r["data"]["message"])

    st, r = call("POST", "/api/v1/metadata/fields", user, {**payload, "field_code": "smoke_user_field"})
    check("USER 创建被拒(403)", st == 403, f"http={st} code={r.get('code')}")

    st, r = call("GET", "/api/v1/metadata/fields/export", admin)
    ok_csv = st == 200 and isinstance(r, str) and r.startswith("\ufeff") and "字段编码" in r
    check("CSV 导出(含 BOM+表头)", ok_csv, f"http={st}")

    st, r = call("DELETE", f"/api/v1/metadata/fields/{new_id}", admin)
    st2, r2 = call("GET", "/api/v1/metadata/fields?keyword=smoke_field_x", admin)
    left = len(r2.get("data", {}).get("list", []))
    check("删除字段(软删)", st == 200 and left == 0, f"remaining={left}")

    print(f"\nRESULT: {len(PASSED)} passed, {len(FAILED)} failed")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
