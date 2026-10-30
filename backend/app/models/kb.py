from datetime import datetime

from sqlalchemy import BigInteger, Column, ForeignKey, Table, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.clock import utc_now


class KbCategory(Base):
    __tablename__ = "kb_category"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0)
    name: Mapped[str] = mapped_column(String(100))
    level: Mapped[int] = mapped_column(Integer, default=1)
    path: Mapped[str] = mapped_column(String(500), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)


class KbEntry(Base):
    __tablename__ = "kb_entry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(BigInteger)
    author_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 知识管理扩展字段（由 sql/knowledge.sql + scripts/run_knowledge.py 维护）
    knowledge_type: Mapped[str] = mapped_column(String(30), default="")
    source_dept: Mapped[str] = mapped_column(String(100), default="")
    keywords: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[int] = mapped_column(Integer, default=1)  # 0=草稿 1=已发布 2=已下线
    publish_at: Mapped[datetime | None] = mapped_column(nullable=True)
    visibility: Mapped[int] = mapped_column(Integer, default=0)  # 0=私有 1=公开
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(insert_default=utc_now, onupdate=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)

    tags: Mapped[list["KbTag"]] = relationship(
        secondary="kb_entry_tag", lazy="selectin"
    )
    attachments: Mapped[list["KbAttachment"]] = relationship(
        primaryjoin="and_(KbAttachment.entry_id == KbEntry.id, KbAttachment.is_deleted == 0)",
        lazy="selectin",
    )


class KbTag(Base):
    __tablename__ = "kb_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)


kb_entry_tag = Table(
    "kb_entry_tag",
    Base.metadata,
    Column("entry_id", BigInteger, ForeignKey("kb_entry.id"), primary_key=True),
    Column("tag_id", BigInteger, ForeignKey("kb_tag.id"), primary_key=True),
)


class KbAttachment(Base):
    __tablename__ = "kb_attachment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kb_entry.id"))
    uploader_id: Mapped[int] = mapped_column(BigInteger)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)


class SysAnnouncement(Base):
    """公告 / 轮播图（type: 1=公告 2=轮播图）"""

    __tablename__ = "sys_announcement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[int] = mapped_column(default=1)
    publisher_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)
