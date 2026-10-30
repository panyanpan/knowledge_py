from fastapi import APIRouter, Depends

from app.core.deps import require_role
from app.core.response import ok

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/ping", summary="RBAC 演示：仅 ADMIN 可访问")
def admin_ping(user=Depends(require_role("ADMIN"))):
    return ok({"hello": user.username, "role": user.role.code})
