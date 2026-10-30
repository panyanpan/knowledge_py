"""知识服务市场 HTTP 冒烟。"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

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
    st, r = call("GET", "/api/v1/services/options", admin)
    d = r.get("data") or {}
    check("options", st == 200 and "API" in d.get("svc_types", []) and len(d.get("statuses", [])) == 2)

    # 2. stats
    st, r = call("GET", "/api/v1/services/stats", admin)
    d = r.get("data") or {}
    check("统计", st == 200 and d.get("total", 0) >= 6 and d.get("online", 0) >= 6 and d.get("month_new", 0) >= 2,
          f"total={d.get('total')} online={d.get('online')} month_new={d.get('month_new')}")

    # 3. 列表
    st, r = call("GET", "/api/v1/services?page=1&page_size=10", admin)
    d = r.get("data") or {}
    rows = d.get("list", [])
    check("列表", st == 200 and len(rows) == 6 and rows[0]["svc_code"] == "SVC-001")

    # 4. 类型筛选
    st, r = call("GET", f"/api/v1/services?svc_type={quote('图谱')}", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("类型筛选", st == 200 and len(rows) == 1 and rows[0]["svc_code"] == "SVC-002")

    # 5. 关键词（按部门）
    st, r = call("GET", f"/api/v1/services?keyword={quote('民政局')}", admin)
    rows = (r.get("data") or {}).get("list", [])
    check("部门关键词", st == 200 and len(rows) == 1 and rows[0]["svc_code"] == "SVC-004")

    # 6. 权限：USER 不能新增
    st, r = call("POST", "/api/v1/services", user, {"svc_name": "越权服务", "svc_type": "API"})
    check("USER无新增权限", st == 403)

    # 7. 新增（自动编码）
    st, r = call("POST", "/api/v1/services", admin, {
        "svc_name": "冒烟测试服务", "svc_type": "工具", "provider_dept": "测试处",
        "description": "临时服务", "tags": "a,b,c", "api_count": 1,
    })
    d = r.get("data") or {}
    check("新增", st == 201 and d.get("svc_code", "").startswith("SVC-") and d.get("status") == 1, f"code={d.get('svc_code')}")
    new_id = d.get("id")

    # 8. 编码冲突
    st, r = call("POST", "/api/v1/services", admin, {"svc_code": "SVC-001", "svc_name": "x", "svc_type": "API"})
    check("编码冲突409", st == 409 and r.get("code") == 2701)

    # 9. 编辑
    st, r = call("PUT", f"/api/v1/services/{new_id}", admin, {"description": "改后的描述", "doc_version": "v0.1"})
    check("编辑", st == 200 and (r.get("data") or {}).get("description") == "改后的描述")

    # 10. 申请调用（USER 可用，已上架）
    st, r = call("POST", "/api/v1/services/apply", user, {
        "service_id": new_id, "apply_dept": "某区政务服务中心", "contact": "张三", "reason": "演示"})
    d = r.get("data") or {}
    check("申请调用(演示回执)", st == 200 and d.get("ticket", "").startswith("SVC-APP-"), f"ticket={d.get('ticket')}")

    # 11. 下架后申请被拒
    call("POST", f"/api/v1/services/{new_id}/toggle", admin)
    st, r = call("POST", "/api/v1/services/apply", user, {"service_id": new_id, "apply_dept": "x"})
    check("下架后申请被拒", st == 400 and r.get("code") == 2703)

    # 12. 已上架不可删除；下架后可删
    call("POST", f"/api/v1/services/{new_id}/toggle", admin)  # 重新上架
    st, r = call("DELETE", f"/api/v1/services/{new_id}", admin)
    check("上架中删除被拒", st == 400 and r.get("code") == 2704)
    call("POST", f"/api/v1/services/{new_id}/toggle", admin)  # 下架
    st, r = call("DELETE", f"/api/v1/services/{new_id}", admin)
    check("下架后删除", st == 200)

    # 13. 不存在
    st, r = call("PUT", "/api/v1/services/99999", admin, {"svc_name": "x"})
    check("404不存在", st == 404 and r.get("code") == 2702)

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
