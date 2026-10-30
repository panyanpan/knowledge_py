"""知识溯源接口：统计 / 检索 / 快捷选项 / 溯源查询 / 环节凭证。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.traces import TraceNodeOut, TraceOut
from app.services import trace_service

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])


@router.get("/stats")
def stats(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(trace_service.stats(db))


@router.get("/options")
def options(_: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """快捷溯源主题（演示阶段为种子主题，待后续对接真实业务场景）。"""
    rows = db.scalars(trace_service.search_traces(db)).all()
    return ok({
        "chips": [{"id": r.id, "title": r.title} for r in rows],
        "secret_levels": ["公开", "内部", "涉密"],
        "chain_status": [
            {"value": 1, "label": "完整可溯源"},
            {"value": 0, "label": "缺失待补录"},
        ],
    })


@router.get("")
def list_traces(
    keyword: str | None = Query(default=None, max_length=100, description="主题/知识编号/场景/溯源编号"),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(trace_service.search_traces(db, keyword=keyword)).all()
    return ok({"list": [TraceOut.model_validate(r).model_dump(mode="json") for r in rows], "total": len(rows)})


@router.get("/{trace_id}")
def trace_detail(
    trace_id: int,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """溯源详情（含环节链路，凭证随环节返回）。"""
    trace = trace_service.get_trace_with_nodes(db, trace_id)
    data = TraceOut.model_validate(trace).model_dump(mode="json")
    data["nodes"] = [TraceNodeOut.model_validate(n).model_dump(mode="json") for n in trace.nodes]
    return ok(data)


@router.post("/{trace_id}/run")
def run_trace(
    trace_id: int,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开始溯源：记录查询留痕并返回元数据 + 链路 + 环节明细。"""
    trace = trace_service.run_trace(db, trace_id)
    data = TraceOut.model_validate(trace).model_dump(mode="json")
    data["nodes"] = [TraceNodeOut.model_validate(n).model_dump(mode="json") for n in trace.nodes]
    return ok(data)
