"""知识溯源 ORM 模型：溯源主体 + 溯源环节。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KbTrace(Base):
    __tablename__ = "kb_trace"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_no: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    entry_no: Mapped[str] = mapped_column(String(50))
    scene: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    version: Mapped[str] = mapped_column(String(20), default="V 1.0")
    dept: Mapped[str] = mapped_column(String(100), default="")
    secret_level: Mapped[str] = mapped_column(String(20), default="公开")
    chain_status: Mapped[int] = mapped_column(Integer, default=1)  # 1完整 0缺失
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    last_query_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)

    nodes: Mapped[list["KbTraceNode"]] = relationship(
        back_populates="trace", order_by="KbTraceNode.step_no"
    )


class KbTraceNode(Base):
    __tablename__ = "kb_trace_node"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("kb_trace.id"))
    step_no: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(50))
    sub: Mapped[str] = mapped_column(String(200), default="")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actor: Mapped[str] = mapped_column(String(100), default="")
    source_ref: Mapped[str] = mapped_column(String(200), default="")
    result: Mapped[str] = mapped_column(String(20), default="")
    result_level: Mapped[str] = mapped_column(String(10), default="green")
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    trace: Mapped["KbTrace"] = relationship(back_populates="nodes")
