"""门户匿名接口：无需登录，仅公开内容。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.response import ok
from app.models.kb import KbCategory, KbEntry, SysAnnouncement
from app.schemas.kb import AnnouncementOut, EntryBrief, EntryOut, PortalCategoryNode
from app.services import entry_service
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])


@router.get("/entries")
def public_entries(
    keyword: str | None = Query(default=None, max_length=100),
    category_id: int | None = None,
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    stmt = select(KbEntry).where(KbEntry.is_deleted == 0, KbEntry.visibility == 1)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(or_(KbEntry.title.like(kw), KbEntry.content.like(kw)))
    if category_id:
        # 含子分类：用物化路径前缀匹配
        cat = db.get(KbCategory, category_id)
        if cat and cat.is_deleted == 0:
            sub_ids = db.scalars(
                select(KbCategory.id).where(
                    KbCategory.is_deleted == 0,
                    or_(KbCategory.id == category_id, KbCategory.path.like(f"{cat.path}/%")),
                )
            ).all()
            stmt = stmt.where(KbEntry.category_id.in_(sub_ids))
        else:
            stmt = stmt.where(KbEntry.category_id == category_id)
    stmt = stmt.order_by(KbEntry.created_at.desc())
    data = paginate(db, stmt, params)
    data["list"] = [EntryBrief.model_validate(r).model_dump() for r in data["list"]]
    return ok(data)


@router.get("/entries/{entry_id}")
def public_entry_detail(
    entry_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    entry = entry_service.get_visible_entry(db, entry_id, user)
    entry.view_count += 1
    db.commit()
    return ok(EntryOut.model_validate(entry).model_dump())


@router.get("/home")
def portal_home(db: Session = Depends(get_db)):
    """门户首页聚合：轮播图、公告、最新、热门、分类导航。"""
    public_cond = (KbEntry.is_deleted == 0, KbEntry.visibility == 1)

    latest = db.scalars(
        select(KbEntry).where(*public_cond).order_by(KbEntry.created_at.desc()).limit(6)
    ).all()
    hot = db.scalars(
        select(KbEntry)
        .where(*public_cond)
        .order_by(KbEntry.view_count.desc(), KbEntry.created_at.desc())
        .limit(6)
    ).all()

    # 公告 / 轮播图：仅已发布，按排序值倒序
    ann_stmt = select(SysAnnouncement).where(
        SysAnnouncement.is_deleted == 0, SysAnnouncement.is_published == 1
    )
    banners = db.scalars(
        ann_stmt.where(SysAnnouncement.type == 2).order_by(SysAnnouncement.sort_order.desc())
    ).all()
    notices = db.scalars(
        ann_stmt.where(SysAnnouncement.type == 1).order_by(
            SysAnnouncement.sort_order.desc(), SysAnnouncement.created_at.desc()
        )
    ).all()

    # 分类导航：仅统计公开条目数，子分类计数向上累加
    counts = dict(
        db.execute(
            select(KbEntry.category_id, func.count())
            .where(*public_cond)
            .group_by(KbEntry.category_id)
        ).all()
    )
    cats = db.scalars(
        select(KbCategory).where(KbCategory.is_deleted == 0).order_by(
            KbCategory.level, KbCategory.sort_order, KbCategory.id
        )
    ).all()

    nodes: dict[int, PortalCategoryNode] = {
        c.id: PortalCategoryNode(id=c.id, name=c.name, level=c.level, entry_count=counts.get(c.id, 0))
        for c in cats
    }
    roots: list[PortalCategoryNode] = []
    for c in cats:  # 已按 level 升序，父节点必先于子节点
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id].children.append(node)
        else:
            roots.append(node)
    # 自底向上累加公开条目数
    def rollup(node: PortalCategoryNode) -> int:
        node.entry_count += sum(rollup(ch) for ch in node.children)
        return node.entry_count

    for r in roots:
        rollup(r)

    return ok(
        {
            "banners": [AnnouncementOut.model_validate(b).model_dump() for b in banners],
            "notices": [AnnouncementOut.model_validate(n).model_dump() for n in notices],
            "latest": [EntryBrief.model_validate(e).model_dump() for e in latest],
            "hot": [EntryBrief.model_validate(e).model_dump() for e in hot],
            "categories": [r.model_dump() for r in roots],
            "stats": {
                "public_entries": db.scalar(
                    select(func.count()).select_from(KbEntry).where(*public_cond)
                )
                or 0,
            },
        }
    )
