"""开发/联调用：为指定用户直接签发 token 并输出前端 kb_auth 结构（不涉及口令）。

用法：./venv/Scripts/python scripts/mint_token.py admin > .tmp_auth.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_token_pair
from app.models.user import SysUser


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    db = SessionLocal()
    try:
        user = db.scalar(select(SysUser).where(SysUser.username == username))
        if user is None:
            print(f"user {username} not found", file=sys.stderr)
            return 1
        role_code = user.role.code if getattr(user, "role", None) else "USER"
        tokens = create_token_pair(user_id=user.id, token_version=user.token_version)
        payload = {
            "tokens": tokens,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role_code": role_code,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else "",
            },
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
