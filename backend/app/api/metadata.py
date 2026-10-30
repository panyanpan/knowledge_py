"""知识元数据管理接口：字段定义 CRUD / 统计 / 规则校验 / CSV 导出。"""
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ok
from app.models.metadata import KbMetadataField
from app.models.user import SysUser
from app.schemas.metadata import (
    DATA_TYPES,
    DOMAINS,
    RULE_TYPES,
    MetadataFieldCreate,
    MetadataFieldOut,
    MetadataFieldUpdate,
)
from app.services import metadata_service
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


@router.get("/options")
def options(_: SysUser = Depends(get_current_user)):
    """前端下拉选项：数据类型 / 元数据域 / 规则类型。"""
    return ok({"data_types": DATA_TYPES, "domains": DOMAINS, "rule_types": RULE_TYPES})


@router.get("/stats")
def stats(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(metadata_service.stats(db))


@router.get("/fields")
def list_fields(
    keyword: str | None = Query(default=None, max_length=100, description="字段名称/编码模糊搜索"),
    domain: str | None = Query(default=None),
    status: int | None = Query(default=None, ge=0, le=1),
    data_type: str | None = Query(default=None),
    params: PageParams = Depends(page_params),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = metadata_service.list_fields(
        db, keyword=keyword, domain=domain, status=status, data_type=data_type
    )
    data = paginate(db, stmt, params)
    data["list"] = [MetadataFieldOut.model_validate(r).model_dump() for r in data["list"]]
    return ok(data)


@router.get("/fields/export")
def export_fields(
    domain: str | None = None,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = metadata_service.list_fields(db, domain=domain)
    rows = db.scalars(stmt).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["序号", "字段名称", "字段编码", "数据类型", "所属元数据域", "是否必填", "状态", "校验规则", "更新时间"])
    for i, r in enumerate(rows, 1):
        writer.writerow(
            [
                i,
                r.field_name,
                r.field_code,
                r.data_type,
                r.domain,
                "必填" if r.is_required else "选填",
                "已启用" if r.status == 1 else "已停用",
                r.rule_type or "未配置",
                r.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    content = "\ufeff" + buf.getvalue()  # BOM 保证 Excel 中文不乱码
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''metadata_fields.csv"},
    )


@router.post("/fields", status_code=201)
def create_field(
    data: MetadataFieldCreate,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    field = metadata_service.create(db, data)
    return ok(MetadataFieldOut.model_validate(field).model_dump(), message="创建成功")


@router.put("/fields/{field_id}")
def update_field(
    field_id: int,
    data: MetadataFieldUpdate,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    field = metadata_service.update(db, field_id, data)
    return ok(MetadataFieldOut.model_validate(field).model_dump(), message="更新成功")


@router.delete("/fields/{field_id}")
def delete_field(
    field_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    metadata_service.delete(db, field_id)
    return ok(None, message="删除成功")


@router.post("/fields/{field_id}/check-rule")
def check_rule(
    field_id: int,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    field: KbMetadataField = metadata_service.get_active(db, field_id)
    return ok(metadata_service.check_rule(field))
