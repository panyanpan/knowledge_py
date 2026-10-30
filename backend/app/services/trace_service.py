"""知识溯源：统计 / 检索 / 溯源查询（记录留痕）/ 环节凭证。

溯源记录由系统自动记存（演示阶段为种子数据），本模块仅提供只读查询与查询留痕。
"""
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.error_codes import biz_error
from app.models.kb import KbEntry
from app.models.trace import KbTrace, KbTraceNode

E_TRACE_NOT_FOUND = (2801, "溯源记录不存在", 404)


def stats(db: Session) -> dict:
    """统计条：已纳管知识条目 / 链路完整 / 链路缺失 / 近30日溯源查询。"""
    managed = (
        db.scalar(select(func.count()).select_from(KbEntry).where(KbEntry.is_deleted == 0)) or 0
    )
    complete = db.scalar(
        select(func.count()).select_from(KbTrace).where(KbTrace.is_deleted == 0, KbTrace.chain_status == 1)
    ) or 0
    missing = db.scalar(
        select(func.count()).select_from(KbTrace).where(KbTrace.is_deleted == 0, KbTrace.chain_status == 0)
    ) or 0
    since = datetime.utcnow() - timedelta(days=30)
    queries_30d = (
        db.scalar(
            select(func.coalesce(func.sum(KbTrace.query_count), 0)).where(
                KbTrace.is_deleted == 0, KbTrace.last_query_at >= since
            )
        )
        or 0
    )
    return {
        "managed_entries": int(managed),
        "chain_complete": int(complete),
        "chain_missing": int(missing),
        "queries_30d": int(queries_30d),
    }


def search_traces(db: Session, *, keyword: str | None = None):
    """按主题名称 / 知识编号 / 业务场景 / 溯源编号检索。"""
    stmt = (
        select(KbTrace)
        .where(KbTrace.is_deleted == 0)
        # MySQL 8.0 不支持 NULLS LAST，用 is_(None) 先排空值
        .order_by(KbTrace.last_query_at.is_(None), KbTrace.last_query_at.desc(), KbTrace.id)
    )
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                KbTrace.title.like(kw),
                KbTrace.entry_no.like(kw),
                KbTrace.scene.like(kw),
                KbTrace.trace_no.like(kw),
            )
        )
    return stmt


def get_trace_with_nodes(db: Session, trace_id: int) -> KbTrace:
    trace = db.scalar(
        select(KbTrace)
        .options(selectinload(KbTrace.nodes))
        .where(KbTrace.id == trace_id, KbTrace.is_deleted == 0)
    )
    if not trace:
        raise biz_error(E_TRACE_NOT_FOUND)
    return trace


def run_trace(db: Session, trace_id: int) -> KbTrace:
    """执行一次溯源查询：留痕（累计次数 +1、最近时间）并返回完整链路。"""
    trace = get_trace_with_nodes(db, trace_id)
    trace.query_count = (trace.query_count or 0) + 1
    trace.last_query_at = datetime.utcnow()
    db.commit()
    db.refresh(trace)
    return trace
