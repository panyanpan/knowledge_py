from datetime import datetime

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.clock import utc_now


class KbService(Base):
    """知识服务市场服务项。"""

    __tablename__ = "kb_service"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    svc_code: Mapped[str] = mapped_column(String(30), unique=True)
    svc_name: Mapped[str] = mapped_column(String(100))
    provider_dept: Mapped[str | None] = mapped_column(String(100), nullable=True)
    svc_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(300), nullable=True)  # 逗号分隔
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    api_count: Mapped[int] = mapped_column(Integer, default=0)
    doc_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    doc_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1)  # 1=已上架 0=已下架
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    creator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(insert_default=utc_now, onupdate=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)
