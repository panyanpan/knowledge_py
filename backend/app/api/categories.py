from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.kb import CategoryCreate, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("")
def tree(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok([n.model_dump() for n in category_service.list_tree(db)])


@router.post("", status_code=201)
def create(data: CategoryCreate, _: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    cat = category_service.create(db, data)
    return ok({"id": cat.id, "name": cat.name, "level": cat.level, "path": cat.path}, message="创建成功")


@router.put("/{category_id}")
def update(category_id: int, data: CategoryUpdate, _: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    cat = category_service.update(db, category_id, data)
    return ok({"id": cat.id, "name": cat.name, "parent_id": cat.parent_id, "level": cat.level, "path": cat.path}, message="更新成功")


@router.delete("/{category_id}")
def remove(category_id: int, _: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    category_service.delete(db, category_id)
    return ok(None, message="删除成功")
