"""知识管理：列表检索 / 统计 / 维护 / 上下架 / 导出。"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.error_codes import biz_error
from app.models.kb import KbCategory, KbEntry
from app.models.user import SysUser
from app.schemas.knowledge import KNOWLEDGE_STATUS, KnowledgeCreate, KnowledgeUpdate
from app.services import entry_service
from app.utils.clock import utc_now
from app.utils.sanitize import sanitize_rich_text

E_KNOWLEDGE_NOT_FOUND = (2501, "知识不存在", 404)
E_KNOWLEDGE_FORBIDDEN = (2502, "无权操作该知识", 403)
E_STATUS_INVALID = (2503, "知识状态不合法", 400)

# 知识管理只面向标注了知识类型的条目，历史录入的普通条目不在此模块出现
MANAGED = KbEntry.knowledge_type != ""


def category_map(db: Session) -> dict[int, str]:
    rows = db.execute(
        select(KbCategory.id, KbCategory.name).where(KbCategory.is_deleted == 0)
    ).all()
    return {i: n for i, n in rows}


def serialize(entry: KbEntry, cats: dict[int, str], *, detail: bool = False) -> dict:
    data = {
        "id": entry.id,
        "title": entry.title,
        "summary": entry.summary,
        "category_id": entry.category_id,
        "category_name": cats.get(entry.category_id, "未分类"),
        "knowledge_type": entry.knowledge_type,
        "source_dept": entry.source_dept or "",
        "keywords": entry.keywords or "",
        "status": entry.status,
        "status_label": KNOWLEDGE_STATUS.get(entry.status, "未知"),
        "visibility": entry.visibility,
        "view_count": entry.view_count,
        "author_id": entry.author_id,
        "publish_at": entry.publish_at,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "tags": [{"id": t.id, "name": t.name} for t in entry.tags],
    }
    if detail:
        data["content"] = entry.content
    return data


def list_query(
    db: Session,
    *,
    keyword: str | None = None,
    knowledge_type: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
):
    stmt = select(KbEntry).where(KbEntry.is_deleted == 0, MANAGED)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                KbEntry.title.like(kw),
                KbEntry.summary.like(kw),
                KbEntry.keywords.like(kw),
                KbEntry.content.like(kw),
            )
        )
    if knowledge_type:
        stmt = stmt.where(KbEntry.knowledge_type == knowledge_type)
    if category_id:
        # 选中父分类时，子分类下的知识一并命中
        children = db.scalars(
            select(KbCategory.id).where(
                KbCategory.is_deleted == 0,
                or_(KbCategory.id == category_id, KbCategory.path.like(f"%/{category_id}/%")),
            )
        ).all()
        stmt = stmt.where(KbEntry.category_id.in_(list(children) or [category_id]))
    if status is not None:
        stmt = stmt.where(KbEntry.status == status)
    return stmt.order_by(KbEntry.updated_at.desc(), KbEntry.id.desc())


def stats(db: Session) -> dict:
    base = select(func.count()).select_from(KbEntry).where(KbEntry.is_deleted == 0, MANAGED)
    total = db.scalar(base) or 0
    published = db.scalar(base.where(KbEntry.status == 1)) or 0
    draft = db.scalar(base.where(KbEntry.status == 0)) or 0
    offline = db.scalar(base.where(KbEntry.status == 2)) or 0
    month_start = db.scalar(select(func.date_format(func.now(), "%Y-%m-01")))
    month_new = db.scalar(base.where(KbEntry.created_at >= month_start)) or 0
    total_views = db.scalar(
        select(func.coalesce(func.sum(KbEntry.view_count), 0)).where(
            KbEntry.is_deleted == 0, MANAGED
        )
    ) or 0
    by_type = db.execute(
        select(KbEntry.knowledge_type, func.count())
        .where(KbEntry.is_deleted == 0, MANAGED)
        .group_by(KbEntry.knowledge_type)
    ).all()
    by_dept = db.execute(
        select(KbEntry.source_dept, func.count())
        .where(KbEntry.is_deleted == 0, MANAGED, KbEntry.source_dept != "")
        .group_by(KbEntry.source_dept)
        .order_by(func.count().desc())
        .limit(6)
    ).all()
    return {
        "total": total,
        "published": published,
        "draft": draft,
        "offline": offline,
        "month_new": month_new,
        "total_views": int(total_views),
        "by_type": {t: c for t, c in by_type},
        "by_dept": {d: c for d, c in by_dept},
    }


def get_active(db: Session, knowledge_id: int) -> KbEntry:
    entry = db.get(KbEntry, knowledge_id)
    if entry is None or entry.is_deleted != 0 or not entry.knowledge_type:
        raise biz_error(E_KNOWLEDGE_NOT_FOUND)
    return entry


def _check_manage(user: SysUser, entry: KbEntry) -> None:
    if not entry_service.can_manage(user, entry):
        raise biz_error(E_KNOWLEDGE_FORBIDDEN)


def create(db: Session, data: KnowledgeCreate, user: SysUser) -> KbEntry:
    entry_service.ensure_category_exists(db, data.category_id)
    entry = KbEntry(
        category_id=data.category_id,
        author_id=user.id,
        title=data.title.strip(),
        content=sanitize_rich_text(data.content) if data.content else None,
        summary=data.summary,
        knowledge_type=data.knowledge_type,
        source_dept=data.source_dept or "",
        keywords=data.keywords or "",
        status=data.status,
        visibility=data.visibility,
        publish_at=utc_now() if data.status == 1 else None,
    )
    entry_service.set_entry_tags(db, entry, data.tag_ids)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update(db: Session, knowledge_id: int, data: KnowledgeUpdate, user: SysUser) -> KbEntry:
    entry = get_active(db, knowledge_id)
    _check_manage(user, entry)
    payload = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    if "category_id" in payload and payload["category_id"] is not None:
        entry_service.ensure_category_exists(db, payload["category_id"])
    if "content" in payload:
        payload["content"] = sanitize_rich_text(payload["content"] or "")
    if "status" in payload and payload["status"] is not None:
        payload["publish_at"] = utc_now() if payload["status"] == 1 else entry.publish_at
    for k, v in payload.items():
        if v is not None or k in ("summary", "content", "source_dept", "keywords"):
            setattr(entry, k, v)
    if data.tag_ids is not None:
        entry_service.set_entry_tags(db, entry, data.tag_ids)
    db.commit()
    db.refresh(entry)
    return entry


def set_status(db: Session, knowledge_id: int, status: int, user: SysUser) -> KbEntry:
    if status not in KNOWLEDGE_STATUS:
        raise biz_error(E_STATUS_INVALID)
    entry = get_active(db, knowledge_id)
    _check_manage(user, entry)
    entry.status = status
    if status == 1:
        entry.publish_at = utc_now()
        entry.visibility = 1  # 已发布的知识同步开放到门户
    elif status == 2:
        entry.visibility = 0
    db.commit()
    db.refresh(entry)
    return entry


def delete(db: Session, knowledge_id: int, user: SysUser) -> None:
    entry = get_active(db, knowledge_id)
    _check_manage(user, entry)
    entry.is_deleted = 1
    db.commit()

