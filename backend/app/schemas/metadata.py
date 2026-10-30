from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

DATA_TYPES = ["string", "enum", "text", "number", "date", "bool"]
DOMAINS = ["基础", "业务", "管理", "技术"]
RULE_TYPES = ["none", "length", "regex", "enum", "range"]


class MetadataFieldCreate(BaseModel):
    field_name: str = Field(min_length=1, max_length=100)
    field_code: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    data_type: str = Field(default="string")
    domain: str = Field(default="基础")
    is_required: int = Field(default=0, ge=0, le=1)
    status: int = Field(default=1, ge=0, le=1)
    description: str | None = Field(default=None, max_length=500)
    rule_type: str | None = Field(default=None)
    rule_config: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("data_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in DATA_TYPES:
            raise ValueError(f"数据类型必须是 {DATA_TYPES} 之一")
        return v

    @field_validator("domain")
    @classmethod
    def _check_domain(cls, v: str) -> str:
        if v not in DOMAINS:
            raise ValueError(f"元数据域必须是 {DOMAINS} 之一")
        return v

    @field_validator("rule_type")
    @classmethod
    def _check_rule_type(cls, v: str | None) -> str | None:
        if v and v not in RULE_TYPES:
            raise ValueError(f"校验规则类型必须是 {RULE_TYPES} 之一")
        return v


class MetadataFieldUpdate(BaseModel):
    field_name: str | None = Field(default=None, min_length=1, max_length=100)
    data_type: str | None = None
    domain: str | None = None
    is_required: int | None = Field(default=None, ge=0, le=1)
    status: int | None = Field(default=None, ge=0, le=1)
    description: str | None = Field(default=None, max_length=500)
    rule_type: str | None = None
    rule_config: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("data_type")
    @classmethod
    def _check_type(cls, v: str | None) -> str | None:
        if v is not None and v not in DATA_TYPES:
            raise ValueError(f"数据类型必须是 {DATA_TYPES} 之一")
        return v

    @field_validator("domain")
    @classmethod
    def _check_domain(cls, v: str | None) -> str | None:
        if v is not None and v not in DOMAINS:
            raise ValueError(f"元数据域必须是 {DOMAINS} 之一")
        return v

    @field_validator("rule_type")
    @classmethod
    def _check_rule_type(cls, v: str | None) -> str | None:
        if v and v not in RULE_TYPES:
            raise ValueError(f"校验规则类型必须是 {RULE_TYPES} 之一")
        return v


class MetadataFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_name: str
    field_code: str
    data_type: str
    domain: str
    is_required: int
    status: int
    description: str | None
    rule_type: str | None
    rule_config: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class RuleCheckResult(BaseModel):
    passed: bool
    issues: list[str] = []
    message: str = ""
