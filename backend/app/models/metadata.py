from datetime import datetime

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.clock import utc_now


class KbMetadataField(Base):
    """知识元数据字段定义。"""

    __tablename__ = "kb_metadata_field"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    field_name: Mapped[str] = mapped_column(String(100))
    field_code: Mapped[str] = mapped_column(String(100), unique=True)
    data_type: Mapped[str] = mapped_column(String(20), default="string")
    domain: Mapped[str] = mapped_column(String(20), default="基础")
    is_required: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rule_config: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(insert_default=utc_now, onupdate=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)
