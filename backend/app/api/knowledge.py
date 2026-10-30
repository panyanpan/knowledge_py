"""知识管理接口：清单检索 / 统计 / 详情 / 维护 / 上下架 / CSV 导出。"""
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.kb import KbCategory
from app.models.user import SysUser
from app.schemas.knowledge import (
    KNOWLEDGE_STATUS,
    KNOWLEDGE_TYPES,
    CategoryOption,
    KnowledgeCreate,
    KnowledgeDetail,
    KnowledgeItem,
    KnowledgeUpdate,
)
from app.services import knowledge_service
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/options")
def options(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """前端下拉选项：知识类型 / 状态 / 分类。"""
    rows = db.scalars(
        select(KbCategory)
        .where(KbCategory.is_deleted == 0)
        .order_by(KbCategory.level.asc(), KbCategory.sort_order.desc(), KbCategory.id.asc())
    ).all()
    return ok(
        {
            "knowledge_types": KNOWLEDGE_TYPES,
            "statuses": {str(k): v for k, v in KNOWLEDGE_STATUS.items()},
            "categories": [
                CategoryOption(id=r.id, name=r.name, level=r.level, path=r.path).model_dump()
                for r in rows
            ],
        }
    )


@router.get("/stats")
def stats(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(knowledge_service.stats(db))


@router.get("/export")
def export_knowledge(
    knowledge_type: str | None = None,
    status: int | None = Query(default=None, ge=0, le=2),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cats = knowledge_service.category_map(db)
    stmt = knowledge_service.list_query(db, knowledge_type=knowledge_type, status=status)
    rows = db.scalars(stmt).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["序号", "知识标题", "知识类型", "所属分类", "来源部门", "关键词", "状态", "浏览量", "更新时间"]
    )
    for i, r in enumerate(rows, 1):
        writer.writerow(
            [
                i,
                r.title,
                r.knowledge_type,
                cats.get(r.category_id, "未分类"),
                r.source_dept,
                r.keywords,
                KNOWLEDGE_STATUS.get(r.status, "未知"),
                r.view_count,
                r.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    content = "\ufeff" + buf.getvalue()  # BOM 保证 Excel 中文不乱码
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''knowledge_list.csv"},
    )


@router.get("")
def list_knowledge(
    keyword: str | None = Query(default=None, max_length=100, description="标题/摘要/关键词/正文"),
    knowledge_type: str | None = Query(default=None, description="知识类型"),
    category_id: int | None = Query(default=None, description="分类（含子分类）"),
    status: int | None = Query(default=None, ge=0, le=2, description="0=草稿 1=已发布 2=已下线"),
    params: PageParams = Depends(page_params),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = knowledge_service.list_query(
        db,
        keyword=keyword,
        knowledge_type=knowledge_type,
        category_id=category_id,
        status=status,
    )
    data = paginate(db, stmt, params)
    cats = knowledge_service.category_map(db)
    data["list"] = [KnowledgeItem(**knowledge_service.serialize(r, cats)).model_dump() for r in data["list"]]
    return ok(data)


@router.post("", status_code=201)
def create_knowledge(
    data: KnowledgeCreate,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = knowledge_service.create(db, data, user)
    cats = knowledge_service.category_map(db)
    item = knowledge_service.serialize(entry, cats, detail=True)
    return ok(KnowledgeDetail(**item).model_dump(), message="创建成功")


@router.get("/{knowledge_id}")
def get_knowledge(
    knowledge_id: int,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = knowledge_service.get_active(db, knowledge_id)
    cats = knowledge_service.category_map(db)
    item = knowledge_service.serialize(entry, cats, detail=True)
    return ok(KnowledgeDetail(**item).model_dump())


@router.put("/{knowledge_id}")
def update_knowledge(
    knowledge_id: int,
    data: KnowledgeUpdate,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = knowledge_service.update(db, knowledge_id, data, user)
    cats = knowledge_service.category_map(db)
    item = knowledge_service.serialize(entry, cats, detail=True)
    return ok(KnowledgeDetail(**item).model_dump(), message="更新成功")


@router.post("/{knowledge_id}/status")
def change_status(
    knowledge_id: int,
    status: int = Query(ge=0, le=2, description="0=草稿 1=已发布 2=已下线"),
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = knowledge_service.set_status(db, knowledge_id, status, user)
    cats = knowledge_service.category_map(db)
    item = knowledge_service.serialize(entry, cats)
    return ok(KnowledgeItem(**item).model_dump(), message=f"已切换为{KNOWLEDGE_STATUS[status]}")


@router.delete("/{knowledge_id}")
def delete_knowledge(
    knowledge_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    knowledge_service.delete(db, knowledge_id, user)
    return ok(None, message="删除成功")
