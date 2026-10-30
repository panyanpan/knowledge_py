from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

SVC_TYPES = ["API", "图谱", "匹配", "订阅", "工具", "交换"]


class ServiceCreate(BaseModel):
    svc_code: str | None = Field(default=None, max_length=30, description="留空则自动生成 SVC-xxx")
    svc_name: str = Field(min_length=1, max_length=100)
    provider_dept: str | None = Field(default=None, max_length=100)
    svc_type: str
    description: str | None = Field(default=None, max_length=500)
    tags: str | None = Field(default=None, max_length=300, description="能力标签，逗号分隔")
    api_count: int = Field(default=0, ge=0, le=999)
    doc_version: str | None = Field(default=None, max_length=20)
    doc_url: str | None = Field(default=None, max_length=300)
    status: int = Field(default=1, ge=0, le=1)

    @field_validator("svc_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in SVC_TYPES:
            raise ValueError(f"服务类型必须是 {SVC_TYPES} 之一")
        return v


class ServiceUpdate(BaseModel):
    svc_name: str | None = Field(default=None, min_length=1, max_length=100)
    provider_dept: str | None = Field(default=None, max_length=100)
    svc_type: str | None = None
    description: str | None = Field(default=None, max_length=500)
    tags: str | None = Field(default=None, max_length=300)
    api_count: int | None = Field(default=None, ge=0, le=999)
    doc_version: str | None = Field(default=None, max_length=20)
    doc_url: str | None = Field(default=None, max_length=300)
    status: int | None = Field(default=None, ge=0, le=1)

    @field_validator("svc_type")
    @classmethod
    def _check_type(cls, v: str | None) -> str | None:
        if v is not None and v not in SVC_TYPES:
            raise ValueError(f"服务类型必须是 {SVC_TYPES} 之一")
        return v


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    svc_code: str
    svc_name: str
    provider_dept: str | None
    svc_type: str
    description: str | None
    tags: str | None
    call_count: int
    api_count: int
    doc_version: str | None
    doc_url: str | None
    status: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ServiceApply(BaseModel):
    """申请调用（演示预留，后续对接审批流 API）。"""
    service_id: int
    apply_dept: str = Field(min_length=1, max_length=100, description="申请部门")
    contact: str | None = Field(default=None, max_length=50, description="联系人")
    reason: str | None = Field(default=None, max_length=500, description="申请用途")
