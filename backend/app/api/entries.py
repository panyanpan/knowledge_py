from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.kb import KbEntry
from app.models.user import SysUser
from app.schemas.kb import EntryBrief, EntryCreate, EntryUpdate, EntryOut
from app.services import entry_service
from app.utils.pagination import PageParams, paginate, page_params
from app.utils.sanitize import sanitize_rich_text

router = APIRouter(prefix="/api/v1/entries", tags=["entries"])


def _brief_list(db: Session, stmt, params: PageParams) -> dict:
    data = paginate(db, stmt, params)
    data["list"] = [EntryBrief.model_validate(r).model_dump() for r in data["list"]]
    return data


@router.get("")
def list_entries(
    keyword: str | None = Query(default=None, max_length=100, description="标题/内容模糊搜索"),
    category_id: int | None = None,
    visibility: int | None = Query(default=None, ge=0, le=1),
    params: PageParams = Depends(page_params),
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(KbEntry).where(KbEntry.is_deleted == 0)
    stmt = entry_service.visible_entry_filter(stmt, user)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(or_(KbEntry.title.like(kw), KbEntry.content.like(kw)))
    if category_id:
        stmt = stmt.where(KbEntry.category_id == category_id)
    if visibility is not None:
        stmt = stmt.where(KbEntry.visibility == visibility)
    stmt = stmt.order_by(KbEntry.created_at.desc())
    return ok(_brief_list(db, stmt, params))


@router.post("", status_code=201)
def create_entry(
    data: EntryCreate,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry_service.ensure_category_exists(db, data.category_id)
    entry = KbEntry(
        category_id=data.category_id,
        author_id=user.id,
        title=data.title,
        content=sanitize_rich_text(data.content) if data.content else None,
        summary=data.summary,
        visibility=data.visibility,
    )
    entry_service.set_entry_tags(db, entry, data.tag_ids)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return ok(EntryOut.model_validate(entry).model_dump(), message="创建成功")


@router.get("/{entry_id}")
def get_entry(
    entry_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = entry_service.get_visible_entry(db, entry_id, user)
    entry.view_count += 1
    db.commit()
    return ok(EntryOut.model_validate(entry).model_dump())


@router.put("/{entry_id}")
def update_entry(
    entry_id: int,
    data: EntryUpdate,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = entry_service.get_active(db, entry_id)
    entry_service.check_manage_permission(user, entry)
    if data.category_id is not None:
        entry_service.ensure_category_exists(db, data.category_id)
        entry.category_id = data.category_id
    if data.title is not None:
        entry.title = data.title
    if data.content is not None:
        entry.content = sanitize_rich_text(data.content)
    if data.summary is not None:
        entry.summary = data.summary
    if data.visibility is not None:
        entry.visibility = data.visibility
    if data.tag_ids is not None:
        entry_service.set_entry_tags(db, entry, data.tag_ids)
    db.commit()
    db.refresh(entry)
    return ok(EntryOut.model_validate(entry).model_dump(), message="更新成功")


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = entry_service.get_active(db, entry_id)
    entry_service.check_manage_permission(user, entry)
    entry.is_deleted = 1
    db.commit()
    return ok(None, message="删除成功")
