"""阶段三冒烟验收：urllib 标准库实现，依赖运行中的后端 127.0.0.1:8000。"""
import io
import json
import mimetypes
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8000"
PASS, FAIL = "\033[92mPASS\033[0m", "\033[91mFAIL\033[0m"
results = []


def call(method, path, body=None, token=None, raw_body=None, headers=None):
    url = BASE + path
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    if raw_body is not None:
        data = raw_body
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def check(name, actual, expect):
    ok_flag = actual == expect
    results.append(ok_flag)
    print(f"{PASS if ok_flag else FAIL} {name}: actual={actual!r} expect={expect!r}")


def login(username, password):
    st, r = call("POST", "/api/v1/auth/login", {"username": username, "password": password})
    assert st == 200 and r["code"] == 0, f"login {username} failed: {r}"
    return r["data"]["tokens"]["access_token"]


# 准备账号：admin + 两个普通用户
admin = login("admin", "Admin@2026")
u1 = login("tester01", "Test@12345")
suffix = uuid.uuid4().hex[:6]
st, r = call("POST", "/api/v1/auth/register", {"username": f"tester02_{suffix}", "password": "Test@12345", "email": f"tester02_{suffix}@example.com"})
u2 = login(f"tester02_{suffix}", "Test@12345")

# 1. 分类树：3 级
st, r = call("POST", "/api/v1/categories", {"name": "研发资料"}, u1); c1 = r["data"]["id"]
st2, r2 = call("POST", "/api/v1/categories", {"name": "后端技术", "parent_id": c1}, u1); c2 = r2["data"]["id"]
st3, r3 = call("POST", "/api/v1/categories", {"name": "FastAPI", "parent_id": c2}, u1); c3 = r3["data"]["id"]
check("1.三级分类创建", (st, st2, st3, r3["data"]["level"]), (201, 201, 201, 3))

# 2. 非法层级/环检测
st, r = call("POST", "/api/v1/categories", {"name": "过深层级", "parent_id": c3}, u1)
check("2.超过5级被拒(此处第4级应成功)", st, 201)
deep3 = r["data"]["id"]
st, _ = call("PUT", f"/api/v1/categories/{c1}", {"parent_id": c2}, u1)
check("2b.移动到自身子分类被拒", (st, _["code"]), (400, 2006))

# 3. 删除非空分类被拒
st, r = call("DELETE", f"/api/v1/categories/{c2}", token=u1)
check("3.删除有子分类的分类被拒", (st, r["code"]), (409, 2002))

# 4. 标签 + 条目（富文本含 script 应被清洗）
call("POST", "/api/v1/tags", {"name": "python"}, u1)
call("POST", "/api/v1/tags", {"name": "后端"}, u1)
st, tags = call("GET", "/api/v1/tags", token=u1)
tag_ids = [t["id"] for t in tags["data"]][:2]
evil_html = '<p>正常内容</p><script>alert(1)</script><img src="x" onerror="alert(2)">'
st, r = call("POST", "/api/v1/entries", {
    "category_id": c3, "title": f"FastAPI 入门_{suffix}", "content": evil_html,
    "summary": "入门教程", "visibility": 1, "tag_ids": tag_ids,
}, u1)
check("4.创建公开条目", st, 201)
entry_pub = r["data"]["id"]
check("4b.script被清洗", "<script" in r["data"]["content"] or "onerror" in r["data"]["content"], False)

# 5. 私有条目（u2 创建）
st, r = call("POST", "/api/v1/entries", {"category_id": c3, "title": f"私有笔记_{suffix}", "content": "<p>秘密</p>", "visibility": 0}, u2)
entry_priv = r["data"]["id"]

# 6. 附件上传
payload = b"KB-ATTACHMENT-SMOKE-%s" % uuid.uuid4().hex.encode()
boundary = "----kbsmoke"
mp = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"notes.txt\"\r\n"
      f"Content-Type: text/plain\r\n\r\n").encode() + payload + f"\r\n--{boundary}--\r\n".encode()
st, r = call("POST", f"/api/v1/attachments?entry_id={entry_pub}", token=u1,
             raw_body=mp, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
check("6.附件上传", (st, r["code"]), (201, 0))
att_id = r["data"]["id"]

# 7. 搜索命中（标题）
from urllib.parse import quote
st, r = call("GET", f"/api/v1/entries?keyword={quote(f'FastAPI 入门_{suffix}')}", token=u1)
check("7.关键词搜索命中", (st, r["data"]["total"] >= 1), (200, True))

# 8. 匿名可见性：公开条目 200 / 私有条目 404
st, r = call("GET", f"/api/v1/portal/entries/{entry_pub}")
st_priv, _ = call("GET", f"/api/v1/portal/entries/{entry_priv}")
check("8.匿名读公开条目/私有条目404", (st, st_priv), (200, 404))

# 9. 匿名门户列表仅公开
st, r = call("GET", "/api/v1/portal/entries?page_size=100")
ids = [e["id"] for e in r["data"]["list"]]
check("9.匿名门户列表不含私有", entry_priv not in ids, True)

# 10. u2 访问 u1 的公开条目 OK；u1 改 u2 私有条目 → 403；u1 删 u2 私有条目 → 403
st, _ = call("GET", f"/api/v1/entries/{entry_pub}", token=u2)
st_put, _ = call("PUT", f"/api/v1/entries/{entry_priv}", {"title": "hijack"}, u1)
st_del, _ = call("DELETE", f"/api/v1/entries/{entry_priv}", token=u1)
check("10.他人条目改/删被拒403", (st, st_put, st_del), (200, 403, 403))

# 11. ADMIN 可管理他人条目
st, _ = call("PUT", f"/api/v1/entries/{entry_priv}", {"title": f"管理员改名_{suffix}"}, admin)
check("11.ADMIN可改他人条目", st, 200)

# 12. 可见性修改后匿名可读 + 删除校验
st, _ = call("PUT", f"/api/v1/entries/{entry_priv}", {"visibility": 1}, u2)
st2, _ = call("GET", f"/api/v1/portal/entries/{entry_priv}")
check("12.私有转公开后匿名可读", (st, st2), (200, 200))

# 13. 附件下载与删除
req = urllib.request.Request(BASE + f"/api/v1/attachments/{att_id}/download", headers={"Authorization": f"Bearer {u1}"})
with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read()
check("13.附件下载内容一致", content == payload, True)

st, r = call("DELETE", f"/api/v1/attachments/{att_id}", token=u2)
check("13b.他人删附件被拒", (st, r["code"]), (403, 2102))

# 14. 分页返回结构
st, r = call("GET", "/api/v1/entries?page=1&page_size=5", token=u1)
check("14.分页结构", sorted(r["data"].keys()), ["list", "page", "page_size", "total"])

print("\n========== 阶段三冒烟结果:", f"{sum(results)}/{len(results)} 通过", "==========")
raise SystemExit(0 if all(results) else 1)
