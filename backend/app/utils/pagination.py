from dataclasses import dataclass

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db

MAX_PAGE_SIZE = 100


@dataclass
class PageParams:
    page: int
    page_size: int
    offset: int


def page_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=MAX_PAGE_SIZE, description="每页条数"),
) -> PageParams:
    return PageParams(page=page, page_size=page_size, offset=(page - 1) * page_size)


def paginate(db: Session, stmt: Select, params: PageParams) -> dict:
    """对 select 语句统一分页：过滤下推到 SQL，不在应用层捞全表。"""
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset(params.offset).limit(params.page_size)).all()
    return {"list": rows, "total": total or 0, "page": params.page, "page_size": params.page_size}
