from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# 知识类型（与分类树一一对应，便于按类型聚合与统计）
KNOWLEDGE_TYPES = ["事项知识", "政策法规", "一件事知识", "办事指南", "常见问答", "数据标准"]
KNOWLEDGE_STATUS = {0: "草稿", 1: "已发布", 2: "已下线"}


def _check_type(v: str) -> str:
    if v not in KNOWLEDGE_TYPES:
        raise ValueError(f"知识类型必须是 {KNOWLEDGE_TYPES} 之一")
    return v


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category_id: int = Field(ge=1)
    knowledge_type: str = Field(default="事项知识")
    summary: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=500_000, description="富文本 HTML")
    source_dept: str | None = Field(default=None, max_length=100)
    keywords: str | None = Field(default=None, max_length=255, description="英文逗号分隔")
    status: int = Field(default=1, ge=0, le=2)
    visibility: int = Field(default=1, ge=0, le=1, description="0=私有 1=公开")
    tag_ids: list[int] = Field(default_factory=list, max_length=20)

    @field_validator("knowledge_type")
    @classmethod
    def _type_ok(cls, v: str) -> str:
        return _check_type(v)


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category_id: int | None = Field(default=None, ge=1)
    knowledge_type: str | None = None
    summary: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=500_000)
    source_dept: str | None = Field(default=None, max_length=100)
    keywords: str | None = Field(default=None, max_length=255)
    status: int | None = Field(default=None, ge=0, le=2)
    visibility: int | None = Field(default=None, ge=0, le=1)
    tag_ids: list[int] | None = Field(default=None, max_length=20)

    @field_validator("knowledge_type")
    @classmethod
    def _type_ok(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _check_type(v)


class KnowledgeTag(BaseModel):
    id: int
    name: str


class KnowledgeItem(BaseModel):
    """列表项：不含正文，减少传输量。"""

    id: int
    title: str
    summary: str | None
    category_id: int
    category_name: str
    knowledge_type: str
    source_dept: str
    keywords: str
    status: int
    status_label: str
    visibility: int
    view_count: int
    author_id: int
    publish_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[KnowledgeTag] = []


class KnowledgeDetail(KnowledgeItem):
    content: str | None


class KnowledgeStats(BaseModel):
    total: int
    published: int
    draft: int
    offline: int
    month_new: int
    total_views: int
    by_type: dict[str, int] = {}
    by_dept: dict[str, int] = {}


class CategoryOption(BaseModel):
    id: int
    name: str
    level: int
    path: str


class KnowledgeOptions(BaseModel):
    knowledge_types: list[str]
    statuses: dict[str, str]
    categories: list[CategoryOption]
