from datetime import datetime

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.clock import utc_now


class KbRule(Base):
    """知识质量规则。"""

    __tablename__ = "kb_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(30), unique=True)
    rule_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(20))
    scope_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    condition_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=2)  # 1=启用 0=停用 2=待复核
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    creator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(insert_default=utc_now, onupdate=utc_now)
    is_deleted: Mapped[int] = mapped_column(default=0)
