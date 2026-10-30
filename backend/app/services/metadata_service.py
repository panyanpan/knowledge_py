"""知识元数据字段：查询 / 维护 / 校验规则检查。"""
import json
import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.metadata import KbMetadataField
from app.schemas.metadata import MetadataFieldCreate, MetadataFieldUpdate

E_CODE_TAKEN = (2401, "字段编码已存在", 409)
E_FIELD_NOT_FOUND = (2402, "元数据字段不存在", 404)
E_RULE_INVALID = (2403, "校验规则不合法", 400)


def list_fields(
    db: Session,
    *,
    keyword: str | None = None,
    domain: str | None = None,
    status: int | None = None,
    data_type: str | None = None,
):
    stmt = select(KbMetadataField).where(KbMetadataField.is_deleted == 0)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(KbMetadataField.field_name.like(kw), KbMetadataField.field_code.like(kw))
        )
    if domain:
        stmt = stmt.where(KbMetadataField.domain == domain)
    if status is not None:
        stmt = stmt.where(KbMetadataField.status == status)
    if data_type:
        stmt = stmt.where(KbMetadataField.data_type == data_type)
    return stmt.order_by(KbMetadataField.sort_order.desc(), KbMetadataField.id.asc())


def get_active(db: Session, field_id: int) -> KbMetadataField:
    field = db.get(KbMetadataField, field_id)
    if field is None or field.is_deleted != 0:
        from app.core.error_codes import biz_error

        raise biz_error(E_FIELD_NOT_FOUND)
    return field


def _ensure_code_unique(db: Session, code: str, exclude_id: int | None = None) -> None:
    from app.core.error_codes import biz_error

    stmt = select(KbMetadataField.id).where(
        KbMetadataField.field_code == code, KbMetadataField.is_deleted == 0
    )
    if exclude_id:
        stmt = stmt.where(KbMetadataField.id != exclude_id)
    if db.scalar(stmt):
        raise biz_error(E_CODE_TAKEN)


def create(db: Session, data: MetadataFieldCreate) -> KbMetadataField:
    _ensure_code_unique(db, data.field_code)
    field = KbMetadataField(**data.model_dump())
    if field.rule_type in (None, "", "none"):
        field.rule_type = None
        field.rule_config = None
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def update(db: Session, field_id: int, data: MetadataFieldUpdate) -> KbMetadataField:
    field = get_active(db, field_id)
    payload = data.model_dump(exclude_unset=True)
    if payload.get("rule_type") in ("", "none"):
        payload["rule_type"] = None
        payload["rule_config"] = None
    for k, v in payload.items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


def delete(db: Session, field_id: int) -> None:
    field = get_active(db, field_id)
    field.is_deleted = 1
    db.commit()


def stats(db: Session) -> dict:
    base = select(func.count()).select_from(KbMetadataField).where(
        KbMetadataField.is_deleted == 0
    )
    total = db.scalar(base) or 0
    enabled = db.scalar(base.where(KbMetadataField.status == 1)) or 0
    required = db.scalar(base.where(KbMetadataField.is_required == 1)) or 0
    # 待校验 = 已启用但未配置校验规则
    pending = (
        db.scalar(
            base.where(
                KbMetadataField.status == 1,
                or_(KbMetadataField.rule_type.is_(None), KbMetadataField.rule_type == ""),
            )
        )
        or 0
    )
    domains = db.execute(
        select(KbMetadataField.domain, func.count())
        .where(KbMetadataField.is_deleted == 0)
        .group_by(KbMetadataField.domain)
    ).all()
    return {
        "total": total,
        "enabled": enabled,
        "disabled": total - enabled,
        "required": required,
        "pending": pending,
        "domains": {d: c for d, c in domains},
    }


def check_rule(field: KbMetadataField) -> dict:
    """校验字段自身的规则配置是否可用（不校验业务数据，只校验规则合法性）。"""
    issues: list[str] = []
    rule_type = (field.rule_type or "").strip()
    raw = (field.rule_config or "").strip()

    if not rule_type or rule_type == "none":
        return {
            "passed": False,
            "issues": ["未配置校验规则"],
            "message": "该字段尚未配置校验规则，建议补充后再启用",
        }

    cfg: dict = {}
    if not raw:
        issues.append("规则参数为空")
    else:
        try:
            cfg = json.loads(raw)
            if not isinstance(cfg, dict):
                issues.append("规则参数必须是 JSON 对象")
                cfg = {}
        except json.JSONDecodeError as exc:
            issues.append(f"规则参数不是合法 JSON：{exc.msg}")

    if cfg:
        if rule_type == "length":
            mn, mx = cfg.get("min"), cfg.get("max")
            if not isinstance(mn, int) or not isinstance(mx, int):
                issues.append("长度规则需要整数 min / max")
            elif mn < 0 or mx <= 0 or mn > mx:
                issues.append(f"长度区间不合法：min={mn}, max={mx}")
        elif rule_type == "regex":
            pattern = cfg.get("pattern")
            if not isinstance(pattern, str) or not pattern:
                issues.append("正则规则缺少 pattern")
            else:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    issues.append(f"正则表达式无法编译：{exc}")
        elif rule_type == "enum":
            options = cfg.get("options") or cfg.get("source")
            if not options:
                issues.append("枚举规则需要 options 或 source")
            elif isinstance(options, list):
                if not options or not all(isinstance(o, str) and o.strip() for o in options):
                    issues.append("枚举选项必须是非空字符串数组")
                elif len(set(options)) != len(options):
                    issues.append("枚举选项存在重复值")
        elif rule_type == "range":
            mn, mx = cfg.get("min"), cfg.get("max")
            if not isinstance(mn, (int, float)) or not isinstance(mx, (int, float)):
                issues.append("数值区间需要数字 min / max")
            elif mn > mx:
                issues.append(f"数值区间不合法：min={mn}, max={mx}")

    passed = not issues
    return {
        "passed": passed,
        "issues": issues,
        "message": "规则有效，未发现冲突" if passed else "；".join(issues),
    }
