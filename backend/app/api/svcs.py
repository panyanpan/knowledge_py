"""知识服务市场接口：服务清单 / 新增 / 编辑 / 上下架 / 删除 / 申请调用（演示）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.svcs import SVC_TYPES, ServiceApply, ServiceCreate, ServiceOut, ServiceUpdate
from app.services import svc_service
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/services", tags=["services"])


@router.get("/options")
def options(_: SysUser = Depends(get_current_user)):
    """前端下拉选项：服务类型 / 状态。"""
    return ok({
        "svc_types": SVC_TYPES,
        "statuses": [
            {"value": 1, "label": "已上架"},
            {"value": 0, "label": "已下架"},
        ],
    })


@router.get("/stats")
def stats(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(svc_service.stats(db))


@router.get("")
def list_services(
    keyword: str | None = Query(default=None, max_length=100, description="服务名称/编码/部门模糊搜索"),
    svc_type: str | None = Query(default=None),
    status: int | None = Query(default=None, ge=0, le=1),
    params: PageParams = Depends(page_params),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = svc_service.list_services(db, keyword=keyword, svc_type=svc_type, status=status)
    data = paginate(db, stmt, params)
    data["list"] = [ServiceOut.model_validate(r).model_dump(mode="json") for r in data["list"]]
    return ok(data)


@router.post("", status_code=201)
def create_service(
    data: ServiceCreate,
    current: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    svc = svc_service.create(db, data, creator_id=current.id)
    return ok(ServiceOut.model_validate(svc).model_dump(mode="json"), message="创建成功")


@router.put("/{svc_id}")
def update_service(
    svc_id: int,
    data: ServiceUpdate,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    svc = svc_service.update(db, svc_id, data)
    return ok(ServiceOut.model_validate(svc).model_dump(mode="json"), message="更新成功")


@router.delete("/{svc_id}")
def delete_service(
    svc_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    svc_service.delete(db, svc_id)
    return ok(None, message="删除成功")


@router.post("/{svc_id}/toggle")
def toggle_service(
    svc_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    svc = svc_service.toggle(db, svc_id)
    return ok(ServiceOut.model_validate(svc).model_dump(mode="json"), message="状态已更新")


@router.post("/apply")
def apply_service(
    data: ServiceApply,
    current: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """申请调用（演示预留）：返回受理回执，审批流后续对接 API。"""
    svc = svc_service.get_active(db, data.service_id)
    return ok(svc_service.apply_demo(db, svc, data.apply_dept, data.contact, data.reason))
