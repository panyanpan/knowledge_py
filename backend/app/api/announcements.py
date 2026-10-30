"""公告 / 轮播图维护接口（仅 ADMIN）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.error_codes import biz_error
from app.core.response import ok
from app.models.kb import SysAnnouncement
from app.models.user import SysUser
from app.schemas.kb import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])

E_ANN_NOT_FOUND = (2301, "公告不存在", 404)


@router.get("")
def list_announcements(
    type: int | None = Query(default=None, ge=1, le=2),
    params: PageParams = Depends(page_params),
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    stmt = select(SysAnnouncement).where(SysAnnouncement.is_deleted == 0)
    if type:
        stmt = stmt.where(SysAnnouncement.type == type)
    stmt = stmt.order_by(SysAnnouncement.sort_order.desc(), SysAnnouncement.created_at.desc())
    data = paginate(db, stmt, params)
    data["list"] = [AnnouncementOut.model_validate(r).model_dump() for r in data["list"]]
    return ok(data)


@router.post("", status_code=201)
def create_announcement(
    data: AnnouncementCreate,
    user: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    ann = SysAnnouncement(
        type=data.type,
        title=data.title,
        content=data.content,
        image_url=data.image_url,
        link_url=data.link_url,
        sort_order=data.sort_order,
        is_published=data.is_published,
        publisher_id=user.id,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ok(AnnouncementOut.model_validate(ann).model_dump(), message="创建成功")


@router.put("/{ann_id}")
def update_announcement(
    ann_id: int,
    data: AnnouncementUpdate,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    ann = db.get(SysAnnouncement, ann_id)
    if ann is None or ann.is_deleted != 0:
        raise biz_error(E_ANN_NOT_FOUND)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ann, field, value)
    db.commit()
    db.refresh(ann)
    return ok(AnnouncementOut.model_validate(ann).model_dump(), message="更新成功")


@router.delete("/{ann_id}")
def delete_announcement(
    ann_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    ann = db.get(SysAnnouncement, ann_id)
    if ann is None or ann.is_deleted != 0:
        raise biz_error(E_ANN_NOT_FOUND)
    ann.is_deleted = 1
    db.commit()
    return ok(None, message="删除成功")
