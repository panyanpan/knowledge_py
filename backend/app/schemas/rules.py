from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

RULE_TYPES = ["时效性", "完整性", "一致性", "重复度", "安全合规", "规范性"]
STATUS_ENABLED = 1
STATUS_DISABLED = 0
STATUS_PENDING = 2
STATUSES = [STATUS_ENABLED, STATUS_DISABLED, STATUS_PENDING]


class RuleCreate(BaseModel):
    rule_code: str | None = Field(default=None, max_length=30, description="留空则自动生成 R-xxx")
    rule_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)
    rule_type: str
    scope_text: str | None = Field(default=None, max_length=200)
    condition_text: str | None = Field(default=None, max_length=500)
    status: int = Field(default=STATUS_PENDING, description="新增默认进入待复核")

    @field_validator("rule_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in RULE_TYPES:
            raise ValueError(f"规则类型必须是 {RULE_TYPES} 之一")
        return v

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: int) -> int:
        if v not in STATUSES:
            raise ValueError("状态必须是 0(停用)/1(启用)/2(待复核)")
        return v


class RuleUpdate(BaseModel):
    rule_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)
    rule_type: str | None = None
    scope_text: str | None = Field(default=None, max_length=200)
    condition_text: str | None = Field(default=None, max_length=500)
    status: int | None = None

    @field_validator("rule_type")
    @classmethod
    def _check_type(cls, v: str | None) -> str | None:
        if v is not None and v not in RULE_TYPES:
            raise ValueError(f"规则类型必须是 {RULE_TYPES} 之一")
        return v

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: int | None) -> int | None:
        if v is not None and v not in STATUSES:
            raise ValueError("状态必须是 0(停用)/1(启用)/2(待复核)")
        return v


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str
    rule_name: str
    description: str | None
    rule_type: str
    scope_text: str | None
    condition_text: str | None
    hit_count: int
    run_count: int
    last_run_at: datetime | None
    status: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class RuleRunResult(BaseModel):
    rule_code: str
    rule_name: str
    scanned: int
    hits: int
    ran_at: datetime
    message: str
