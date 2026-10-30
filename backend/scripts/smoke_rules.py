"""知识规则管理 HTTP 冒烟。"""
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

    # 1. options
    st, r = call("GET", "/api/v1/rules/options", admin)
    d = r.get("data") or {}
    check("options", st == 200 and "时效性" in d.get("rule_types", []) and len(d.get("statuses", [])) == 3)

    # 2. 列表
    st, r = call("GET", "/api/v1/rules?page=1&page_size=10", admin)
    d = r.get("data") or {}
    rows = d.get("list", [])
    check("列表分页", st == 200 and d.get("total", 0) >= 12 and len(rows) == 10, f"total={d.get('total')}")
    first = rows[0] if rows else {}

    # 3. 关键词
    from urllib.parse import quote

    st, r = call("GET", f"/api/v1/rules?keyword={quote('政策时效')}", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("关键词搜索", st == 200 and len(rows) == 1 and rows[0]["rule_code"] == "R-012")

    # 4. 类型筛选
    st, r = call("GET", f"/api/v1/rules?rule_type={quote('一致性')}&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("类型筛选", st == 200 and rows and all(x["rule_type"] == "一致性" for x in rows), f"count={len(rows)}")

    # 5. 状态筛选
    st, r = call("GET", "/api/v1/rules?status=0&page_size=50", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("状态筛选(停用)", st == 200 and rows and all(x["status"] == 0 for x in rows), f"count={len(rows)}")

    # 6. 权限：USER 不能新增
    st, r = call("POST", "/api/v1/rules", user, {"rule_name": "越权规则", "rule_type": "一致性"})
    check("USER无新增权限", st == 403)

    # 7. 新增（自动编码）
    st, r = call("POST", "/api/v1/rules", admin, {
        "rule_name": "冒烟测试规则",
        "description": "冒烟临时规则",
        "rule_type": "规范性",
        "scope_text": "全量知识",
        "condition_text": "标题长度 ≥ 6 字",
    })
    d = r.get("data") or {}
    check("新增进入待复核", st == 201 and d.get("status") == 2 and d.get("rule_code", "").startswith("R-"), f"code={d.get('rule_code')}")
    new_id = d.get("id")

    # 8. 编码冲突
    st, r = call("POST", "/api/v1/rules", admin, {"rule_code": "R-012", "rule_name": "重复编码", "rule_type": "一致性"})
    check("编码冲突409", st == 409 and r.get("code") == 2601)

    # 9. 编辑
    st, r = call("PUT", f"/api/v1/rules/{new_id}", admin, {"condition_text": "标题长度 ≥ 8 字", "rule_type": "完整性"})
    check("编辑", st == 200 and (r.get("data") or {}).get("condition_text") == "标题长度 ≥ 8 字")

    # 10. 试运行
    st, r = call("POST", f"/api/v1/rules/{new_id}/run", user)
    d = r.get("data") or {}
    check("试运行(USER可执行)", st == 200 and d.get("scanned", 0) > 0 and "hits" in d, f"scanned={d.get('scanned')} hits={d.get('hits')}")
    st2, r2 = call("POST", f"/api/v1/rules/{new_id}/run", user)
    check("试运行结果当日稳定", (r2.get("data") or {}).get("hits") == d.get("hits"))

    # 11. 启用（待复核→启用）
    st, r = call("POST", f"/api/v1/rules/{new_id}/toggle", admin)
    check("待复核→启用", st == 200 and (r.get("data") or {}).get("status") == 1)

    # 12. 启用中不可删除
    st, r = call("DELETE", f"/api/v1/rules/{new_id}", admin)
    check("启用中删除被拒", st == 400 and r.get("code") == 2603)

    # 13. 停用后删除
    call("POST", f"/api/v1/rules/{new_id}/toggle", admin)
    st, r = call("DELETE", f"/api/v1/rules/{new_id}", admin)
    check("停用后删除", st == 200)
    st, r = call("GET", f"/api/v1/rules?keyword={quote('冒烟测试规则')}", admin)
    check("删除后不可见", st == 200 and not (r.get("data") or {}).get("list"))

    # 14. 不存在
    st, r = call("PUT", "/api/v1/rules/99999", admin, {"rule_name": "x"})
    check("404不存在", st == 404 and r.get("code") == 2602)

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
