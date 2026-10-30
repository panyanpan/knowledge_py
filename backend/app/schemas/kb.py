from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 分类 ----------
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int = Field(default=0, ge=0, description="0=顶级")
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = Field(default=None, ge=0)
    sort_order: int | None = Field(default=None, ge=0)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    name: str
    level: int
    path: str
    sort_order: int
    created_at: datetime


class CategoryTreeNode(CategoryOut):
    children: list["CategoryTreeNode"] = []


# ---------- 标签 ----------
class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ---------- 条目 ----------
class EntryCreate(BaseModel):
    category_id: int
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=500_000, description="富文本 HTML")
    summary: str | None = Field(default=None, max_length=500)
    visibility: int = Field(default=0, ge=0, le=1, description="0=私有 1=公开")
    tag_ids: list[int] = Field(default_factory=list, max_length=20)


class EntryUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=500_000)
    summary: str | None = Field(default=None, max_length=500)
    visibility: int | None = Field(default=None, ge=0, le=1)
    tag_ids: list[int] | None = Field(default=None, max_length=20)


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_size: int
    mime_type: str


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    author_id: int
    title: str
    content: str | None
    summary: str | None
    visibility: int
    view_count: int
    created_at: datetime
    tags: list[TagOut] = []
    attachments: list[AttachmentOut] = []


class EntryBrief(BaseModel):
    """列表摘要：不含富文本正文。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    author_id: int
    title: str
    summary: str | None
    visibility: int
    view_count: int
    created_at: datetime
    tags: list[TagOut] = []


# ---------- 公告 / 轮播图 ----------
class AnnouncementCreate(BaseModel):
    type: int = Field(default=1, ge=1, le=2, description="1=公告 2=轮播图")
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)
    link_url: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0)
    is_published: int = Field(default=1, ge=0, le=1)


class AnnouncementUpdate(BaseModel):
    type: int | None = Field(default=None, ge=1, le=2)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)
    link_url: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0)
    is_published: int | None = Field(default=None, ge=0, le=1)


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: int
    title: str
    content: str | None
    image_url: str | None
    link_url: str | None
    sort_order: int
    is_published: int
    created_at: datetime


class PortalCategoryNode(BaseModel):
    id: int
    name: str
    level: int
    entry_count: int = 0
    children: list["PortalCategoryNode"] = []
