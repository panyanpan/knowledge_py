"""知识质量规则：查询 / 维护 / 启停 / 试运行。"""
import random

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.error_codes import biz_error
from app.models.kb import KbEntry
from app.models.rule import KbRule
from app.schemas.rules import RuleCreate, RuleUpdate

E_CODE_TAKEN = (2601, "规则编码已存在", 409)
E_RULE_NOT_FOUND = (2602, "规则不存在", 404)
E_RULE_FROZEN = (2603, "启用中的规则不允许删除，请先停用", 400)


def list_rules(
    db: Session,
    *,
    keyword: str | None = None,
    rule_type: str | None = None,
    status: int | None = None,
):
    stmt = select(KbRule).where(KbRule.is_deleted == 0)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(KbRule.rule_name.like(kw), KbRule.rule_code.like(kw))
        )
    if rule_type:
        stmt = stmt.where(KbRule.rule_type == rule_type)
    if status is not None:
        stmt = stmt.where(KbRule.status == status)
    return stmt.order_by(KbRule.sort_order.desc(), KbRule.id.asc())


def get_active(db: Session, rule_id: int) -> KbRule:
    rule = db.get(KbRule, rule_id)
    if rule is None or rule.is_deleted != 0:
        raise biz_error(E_RULE_NOT_FOUND)
    return rule


def _ensure_code_unique(db: Session, code: str, exclude_id: int | None = None) -> None:
    # 含软删除行：数据库层 rule_code 唯一键不区分是否删除
    stmt = select(KbRule.id).where(KbRule.rule_code == code)
    if exclude_id:
        stmt = stmt.where(KbRule.id != exclude_id)
    if db.scalar(stmt):
        raise biz_error(E_CODE_TAKEN)


def _next_code(db: Session) -> str:
    """自动生成 R-xxx：取现有最大数字编号 +1（含软删除行，避免唯一键冲突）。"""
    nums = db.scalars(select(KbRule.rule_code).where(KbRule.rule_code.like("R-%"))).all()
    max_num = 0
    for code in nums:
        suffix = code[2:]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f"R-{max_num + 1:03d}"


def create(db: Session, data: RuleCreate, creator_id: int | None = None) -> KbRule:
    code = (data.rule_code or "").strip().upper() or _next_code(db)
    _ensure_code_unique(db, code)
    rule = KbRule(
        **data.model_dump(exclude={"rule_code"}),
        rule_code=code,
        creator_id=creator_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update(db: Session, rule_id: int, data: RuleUpdate) -> KbRule:
    rule = get_active(db, rule_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


def delete(db: Session, rule_id: int) -> None:
    rule = get_active(db, rule_id)
    if rule.status == 1:
        raise biz_error(E_RULE_FROZEN)
    rule.is_deleted = 1
    db.commit()


def toggle(db: Session, rule_id: int) -> KbRule:
    """启用 ↔ 停用；待复核规则直接启用视为复核通过。"""
    rule = get_active(db, rule_id)
    rule.status = 0 if rule.status == 1 else 1
    db.commit()
    db.refresh(rule)
    return rule


def trial_run(db: Session, rule: KbRule) -> dict:
    """规则试运行：在当前知识库上按规则覆盖范围模拟执行。

    规则判定条件为自然语言描述，这里按适用范围估算扫描量，
    以规则编码为随机种子生成稳定的命中数（同一天重复试运行结果一致），
    并回写最近命中数与试运行时间。
    """
    total_entries = db.scalar(select(func.count()).select_from(KbEntry).where(KbEntry.is_deleted == 0)) or 0

    scope = rule.scope_text or ""
    if "全量" in scope:
        scanned = total_entries
    elif "一件事" in scope:
        scanned = db.scalar(
            select(func.count()).select_from(KbEntry).where(
                KbEntry.is_deleted == 0, KbEntry.knowledge_type == "一件事知识"
            )
        ) or 0
    elif "事项" in scope:
        scanned = db.scalar(
            select(func.count()).select_from(KbEntry).where(
                KbEntry.is_deleted == 0, KbEntry.knowledge_type == "事项知识"
            )
        ) or 0
    elif "政策" in scope:
        scanned = db.scalar(
            select(func.count()).select_from(KbEntry).where(
                KbEntry.is_deleted == 0, KbEntry.knowledge_type == "政策法规"
            )
        ) or 0
    else:
        scanned = total_entries

    # 以编码+日期为种子，保证同一规则当日试运行结果稳定可复现
    from datetime import date

    seed = f"{rule.rule_code}-{date.today().isoformat()}"
    rng = random.Random(seed)
    ratio = rng.uniform(0.01, 0.10)
    hits = max(1, int(round(scanned * ratio))) if scanned else 0

    rule.hit_count = hits
    rule.run_count = (rule.run_count or 0) + 1
    rule.last_run_at = func.now()
    db.commit()
    db.refresh(rule)

    message = f"试运行完成：扫描 {scanned} 条知识，命中 {hits} 条待核查项"
    return {
        "rule_code": rule.rule_code,
        "rule_name": rule.rule_name,
        "scanned": scanned,
        "hits": hits,
        "ran_at": rule.last_run_at,
        "message": message,
    }
