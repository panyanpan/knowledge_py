"""知识规则管理接口：规则清单 / 新增 / 编辑 / 启停 / 删除 / 试运行。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.rules import RULE_TYPES, RuleCreate, RuleOut, RuleUpdate
from app.services import rule_service
from app.utils.pagination import PageParams, page_params, paginate

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@router.get("/options")
def options(_: SysUser = Depends(get_current_user)):
    """前端下拉选项：规则类型 / 状态。"""
    return ok({
        "rule_types": RULE_TYPES,
        "statuses": [
            {"value": 1, "label": "启用"},
            {"value": 0, "label": "停用"},
            {"value": 2, "label": "待复核"},
        ],
    })


@router.get("")
def list_rules(
    keyword: str | None = Query(default=None, max_length=100, description="规则名称/编码模糊搜索"),
    rule_type: str | None = Query(default=None),
    status: int | None = Query(default=None),
    params: PageParams = Depends(page_params),
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = rule_service.list_rules(db, keyword=keyword, rule_type=rule_type, status=status)
    data = paginate(db, stmt, params)
    data["list"] = [RuleOut.model_validate(r).model_dump(mode="json") for r in data["list"]]
    return ok(data)


@router.post("", status_code=201)
def create_rule(
    data: RuleCreate,
    current: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    rule = rule_service.create(db, data, creator_id=current.id)
    return ok(RuleOut.model_validate(rule).model_dump(mode="json"), message="创建成功，规则已进入待复核状态")


@router.put("/{rule_id}")
def update_rule(
    rule_id: int,
    data: RuleUpdate,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    rule = rule_service.update(db, rule_id, data)
    return ok(RuleOut.model_validate(rule).model_dump(mode="json"), message="更新成功")


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    rule_service.delete(db, rule_id)
    return ok(None, message="删除成功")


@router.post("/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    _: SysUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    rule = rule_service.toggle(db, rule_id)
    return ok(RuleOut.model_validate(rule).model_dump(mode="json"), message="状态已更新")


@router.post("/{rule_id}/run")
def run_rule(
    rule_id: int,
    _: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """规则试运行：只读模拟执行，不产生整改工单。"""
    rule = rule_service.get_active(db, rule_id)
    return ok(rule_service.trial_run(db, rule))
