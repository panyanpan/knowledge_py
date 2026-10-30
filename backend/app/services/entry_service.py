from sqlalchemy import Select, select

from app.core.error_codes import biz_error
from app.models.kb import KbEntry, KbTag, kb_entry_tag
from app.models.user import SysUser

E_ENTRY_NOT_FOUND = (2101, "条目不存在", 404)
E_FORBIDDEN_ENTRY = (2102, "无权操作该条目", 403)
E_CATEGORY_REQUIRED = (2103, "所属分类不存在", 400)
E_TAG_NOT_FOUND = (2104, "标签不存在", 400)

VISIBILITY_PRIVATE = 0
VISIBILITY_PUBLIC = 1


def get_active(db, entry_id: int) -> KbEntry:
    entry = db.get(KbEntry, entry_id)
    if entry is None or entry.is_deleted != 0:
        raise biz_error(E_ENTRY_NOT_FOUND)
    return entry


def can_manage(user: SysUser | None, entry: KbEntry) -> bool:
    """USER 仅管理自己的条目；ADMIN 全部可管。"""
    if user is None:
        return False
    return user.role.code == "ADMIN" or entry.author_id == user.id


def ensure_category_exists(db, category_id: int) -> None:
    from app.models.kb import KbCategory

    cat = db.scalar(select(KbCategory.id).where(KbCategory.id == category_id, KbCategory.is_deleted == 0))
    if cat is None:
        raise biz_error(E_CATEGORY_REQUIRED)


def resolve_tags(db, tag_ids: list[int]) -> list[KbTag]:
    if not tag_ids:
        return []
    tags = db.scalars(select(KbTag).where(KbTag.id.in_(tag_ids), KbTag.is_deleted == 0)).all()
    if len(tags) != len(set(tag_ids)):
        raise biz_error(E_TAG_NOT_FOUND)
    return list(tags)


def set_entry_tags(db, entry: KbEntry, tag_ids: list[int]) -> None:
    tags = resolve_tags(db, tag_ids)
    entry.tags = tags


def visible_entry_filter(stmt: Select, user: SysUser | None) -> Select:
    """权限下推到 SQL：匿名/USER 只见公开或自己的；ADMIN 全见。"""
    if user is not None and user.role.code == "ADMIN":
        return stmt
    if user is None:
        return stmt.where(KbEntry.visibility == VISIBILITY_PUBLIC)
    return stmt.where((KbEntry.visibility == VISIBILITY_PUBLIC) | (KbEntry.author_id == user.id))


def get_visible_entry(db, entry_id: int, user: SysUser | None) -> KbEntry:
    """详情读取：私有条目对无权者返回 404（不暴露存在性）。"""
    entry = get_active(db, entry_id)
    if entry.visibility != VISIBILITY_PUBLIC and not can_manage(user, entry):
        raise biz_error(E_ENTRY_NOT_FOUND)
    return entry


def check_manage_permission(user: SysUser | None, entry: KbEntry) -> None:
    if not can_manage(user, entry):
        # 有登录但对他人条目操作 → 403；此处 user 必非 None（路由已要求登录）
        raise biz_error(E_FORBIDDEN_ENTRY)
