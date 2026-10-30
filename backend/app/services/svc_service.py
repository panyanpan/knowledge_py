"""知识服务市场：查询 / 维护 / 上下架 / 申请调用（演示）。"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.error_codes import biz_error
from app.models.svc import KbService
from app.schemas.svcs import ServiceCreate, ServiceUpdate

E_CODE_TAKEN = (2701, "服务编码已存在", 409)
E_SVC_NOT_FOUND = (2702, "服务不存在", 404)
E_SVC_OFFLINE = (2703, "服务已下架，不可申请调用", 400)


def list_services(
    db: Session,
    *,
    keyword: str | None = None,
    svc_type: str | None = None,
    status: int | None = None,
):
    stmt = select(KbService).where(KbService.is_deleted == 0)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(KbService.svc_name.like(kw), KbService.svc_code.like(kw), KbService.provider_dept.like(kw))
        )
    if svc_type:
        stmt = stmt.where(KbService.svc_type == svc_type)
    if status is not None:
        stmt = stmt.where(KbService.status == status)
    return stmt.order_by(KbService.sort_order.desc(), KbService.id.asc())


def get_active(db: Session, svc_id: int) -> KbService:
    svc = db.get(KbService, svc_id)
    if svc is None or svc.is_deleted != 0:
        raise biz_error(E_SVC_NOT_FOUND)
    return svc


def _ensure_code_unique(db: Session, code: str, exclude_id: int | None = None) -> None:
    # 含软删除行：数据库层 svc_code 唯一键不区分是否删除
    stmt = select(KbService.id).where(KbService.svc_code == code)
    if exclude_id:
        stmt = stmt.where(KbService.id != exclude_id)
    if db.scalar(stmt):
        raise biz_error(E_CODE_TAKEN)


def _next_code(db: Session) -> str:
    """自动生成 SVC-xxx：取现有最大数字编号 +1（含软删除行）。"""
    nums = db.scalars(select(KbService.svc_code).where(KbService.svc_code.like("SVC-%"))).all()
    max_num = 0
    for code in nums:
        suffix = code[4:]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f"SVC-{max_num + 1:03d}"


def create(db: Session, data: ServiceCreate, creator_id: int | None = None) -> KbService:
    code = (data.svc_code or "").strip().upper() or _next_code(db)
    _ensure_code_unique(db, code)
    svc = KbService(**data.model_dump(exclude={"svc_code"}), svc_code=code, creator_id=creator_id)
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def update(db: Session, svc_id: int, data: ServiceUpdate) -> KbService:
    svc = get_active(db, svc_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(svc, k, v)
    db.commit()
    db.refresh(svc)
    return svc


def delete(db: Session, svc_id: int) -> None:
    svc = get_active(db, svc_id)
    if svc.status == 1:
        raise biz_error((2704, "已上架的服务不允许删除，请先下架", 400))
    svc.is_deleted = 1
    db.commit()


def toggle(db: Session, svc_id: int) -> KbService:
    """上架 ↔ 下架。"""
    svc = get_active(db, svc_id)
    svc.status = 0 if svc.status == 1 else 1
    db.commit()
    db.refresh(svc)
    return svc


def stats(db: Session) -> dict:
    base = select(func.count()).select_from(KbService).where(KbService.is_deleted == 0)
    total = db.scalar(base) or 0
    online = db.scalar(base.where(KbService.status == 1)) or 0
    month_new = db.scalar(
        select(func.count()).select_from(KbService).where(
            KbService.is_deleted == 0,
            func.date_format(KbService.created_at, "%Y-%m") == func.date_format(func.now(), "%Y-%m"),
        )
    ) or 0
    by_type = db.execute(
        select(KbService.svc_type, func.count())
        .where(KbService.is_deleted == 0, KbService.status == 1)
        .group_by(KbService.svc_type)
    ).all()
    total_calls = db.scalar(select(func.sum(KbService.call_count)).where(KbService.is_deleted == 0)) or 0
    return {
        "total": total,
        "online": online,
        "month_new": month_new,
        "total_calls": int(total_calls),
        "by_type": {t: c for t, c in by_type},
    }


def apply_demo(db: Session, svc: KbService, apply_dept: str, contact: str | None, reason: str | None) -> dict:
    """申请调用（演示预留）：当前仅校验并返回受理回执，审批流后续对接 API。"""
    if svc.status != 1:
        raise biz_error(E_SVC_OFFLINE)
    ticket = f"SVC-APP-{svc.svc_code.split('-')[-1]}-{func_now_seed()}"
    return {
        "ticket": ticket,
        "svc_code": svc.svc_code,
        "svc_name": svc.svc_name,
        "apply_dept": apply_dept,
        "contact": contact,
        "message": f"申请已受理（演示）：工单号 {ticket}，审批流 API 对接后可在线跟踪进度",
    }


def func_now_seed() -> str:
    from datetime import datetime

    from app.utils.clock import utc_now

    return utc_now().strftime("%Y%m%d%H%M%S")
