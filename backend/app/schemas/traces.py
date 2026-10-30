"""知识溯源 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TraceNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_no: int
    name: str
    sub: str
    occurred_at: datetime | None = None
    actor: str
    source_ref: str
    result: str
    result_level: str
    evidence: str | None = None


class TraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trace_no: str
    title: str
    entry_no: str
    scene: str
    category: str
    version: str
    dept: str
    secret_level: str
    chain_status: int
    query_count: int
    last_query_at: datetime | None = None
