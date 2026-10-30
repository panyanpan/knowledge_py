from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.error_codes import biz_error
from app.models.kb import KbCategory, KbEntry
from app.schemas.kb import CategoryCreate, CategoryUpdate, CategoryTreeNode
from app.utils.clock import utc_now

MAX_LEVEL = 5
E_CATEGORY_NOT_FOUND = (2001, "分类不存在", 404)
E_CATEGORY_HAS_CHILDREN = (2002, "该分类存在子分类，不能删除", 409)
E_CATEGORY_HAS_ENTRIES = (2003, "该分类下存在知识条目，不能删除", 409)
E_CATEGORY_DEPTH = (2004, f"分类层级不能超过 {MAX_LEVEL} 级", 400)
E_CATEGORY_PARENT_INVALID = (2005, "父分类不存在", 400)
E_CATEGORY_CYCLE = (2006, "不能将分类移动到其自身或其子分类下", 400)


def get_active(db: Session, category_id: int) -> KbCategory:
    cat = db.get(KbCategory, category_id)
    if cat is None or cat.is_deleted != 0:
        raise biz_error(E_CATEGORY_NOT_FOUND)
    return cat


def list_tree(db: Session) -> list[CategoryTreeNode]:
    cats = db.scalars(
        select(KbCategory).where(KbCategory.is_deleted == 0).order_by(KbCategory.sort_order, KbCategory.id)
    ).all()
    nodes = {c.id: CategoryTreeNode.model_validate(c) for c in cats}
    roots: list[CategoryTreeNode] = []
    for c in cats:
        node = nodes[c.id]
        parent = nodes.get(c.parent_id)
        if parent and c.parent_id != c.id:
            parent.children.append(node)
        else:
            roots.append(node)
    return roots


def create(db: Session, data: CategoryCreate) -> KbCategory:
    if data.parent_id == 0:
        parent, level, path_prefix = None, 1, ""
    else:
        parent = get_active(db, data.parent_id)
        level = parent.level + 1
        path_prefix = f"{parent.path}/"
        if level > MAX_LEVEL:
            raise biz_error(E_CATEGORY_DEPTH)

    cat = KbCategory(
        parent_id=data.parent_id,
        name=data.name,
        level=level,
        sort_order=data.sort_order,
    )
    db.add(cat)
    db.flush()  # 取自增 id 用于物化路径
    cat.path = f"{path_prefix}{cat.id}"
    cat.created_at = utc_now()
    db.commit()
    db.refresh(cat)
    return cat


def update(db: Session, category_id: int, data: CategoryUpdate) -> KbCategory:
    cat = get_active(db, category_id)

    if data.parent_id is not None and data.parent_id != cat.parent_id:
        if data.parent_id == cat.id:
            raise biz_error(E_CATEGORY_CYCLE)
        if data.parent_id == 0:
            new_parent, level, path_prefix = None, 1, ""
        else:
            new_parent = get_active(db, data.parent_id)
            # 禁止把分类挂到自己子分类下（形成环）
            if new_parent.path.startswith(f"{cat.path}/"):
                raise biz_error(E_CATEGORY_CYCLE)
            level = new_parent.level + 1
            path_prefix = f"{new_parent.path}/"
        if level > MAX_LEVEL:
            raise biz_error(E_CATEGORY_DEPTH)
        _reparent_subtree(db, cat, level=level, path_prefix=path_prefix, new_parent_id=data.parent_id)

    if data.name is not None:
        cat.name = data.name
    if data.sort_order is not None:
        cat.sort_order = data.sort_order
    db.commit()
    db.refresh(cat)
    return cat


def _reparent_subtree(db: Session, cat: KbCategory, *, level: int, path_prefix: str, new_parent_id: int) -> None:
    """更新该分类及其全部后代的 level 与物化路径。"""
    old_path = cat.path
    cat.parent_id = new_parent_id
    cat.level = level
    cat.path = f"{path_prefix}{cat.id}"

    descendants = db.scalars(
        select(KbCategory).where(KbCategory.is_deleted == 0, KbCategory.path.like(f"{old_path}/%"))
    ).all()
    for d in descendants:
        # 新路径 = 新父路径前缀 + 旧路径去掉旧前缀；新层级 = 新路径中的斜杠深度
        d.path = f"{cat.path}{d.path[len(old_path):]}"
        d.level = d.path.count("/") + 1


def delete(db: Session, category_id: int) -> None:
    cat = get_active(db, category_id)
    has_children = db.scalar(
        select(KbCategory.id).where(KbCategory.parent_id == category_id, KbCategory.is_deleted == 0)
    )
    if has_children:
        raise biz_error(E_CATEGORY_HAS_CHILDREN)
    has_entries = db.scalar(
        select(KbEntry.id).where(KbEntry.category_id == category_id, KbEntry.is_deleted == 0)
    )
    if has_entries:
        raise biz_error(E_CATEGORY_HAS_ENTRIES)
    cat.is_deleted = 1
    db.commit()
