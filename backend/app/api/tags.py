from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.kb import KbTag
from app.models.user import SysUser
from app.schemas.kb import TagCreate

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("")
def list_tags(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    tags = db.scalars(select(KbTag).where(KbTag.is_deleted == 0).order_by(KbTag.name)).all()
    return ok([{"id": t.id, "name": t.name} for t in tags])


@router.post("", status_code=201)
def create_tag(data: TagCreate, _: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.scalar(select(KbTag).where(KbTag.name == data.name, KbTag.is_deleted == 0))
    if existing:
        return ok({"id": existing.id, "name": existing.name}, message="标签已存在")
    tag = KbTag(name=data.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return ok({"id": tag.id, "name": tag.name}, message="创建成功")
