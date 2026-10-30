import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.error_codes import biz_error
from app.core.response import ok
from app.models.kb import KbAttachment, KbEntry
from app.models.user import SysUser
from app.services import entry_service
from app.utils.clock import utc_now

router = APIRouter(prefix="/api/v1/attachments", tags=["attachments"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 扩展名白名单
ALLOWED_EXTS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".rar", ".7z",
}

E_TOO_LARGE = (2201, "文件大小超过 10MB 限制", 413)
E_EXT_NOT_ALLOWED = (2202, "不支持的文件类型", 400)
E_ATTACHMENT_NOT_FOUND = (2203, "附件不存在", 404)
E_ENTRY_REQUIRED = (2103, "所属条目不存在", 404)


def _safe_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise biz_error(E_EXT_NOT_ALLOWED)
    return ext


@router.post("", status_code=201)
async def upload(
    entry_id: int,
    file: UploadFile,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 附件必须挂在当前用户可见且可管理的条目下
    entry = entry_service.get_active(db, entry_id)
    entry_service.check_manage_permission(user, entry)

    ext = _safe_ext(file.filename or "")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise biz_error(E_TOO_LARGE)

    now = utc_now()
    rel_dir = f"{now:%Y/%m}"
    rel_path = f"{rel_dir}/{uuid.uuid4().hex}{ext}"
    abs_path = UPLOAD_DIR / rel_dir
    abs_path.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / rel_path).write_bytes(content)

    att = KbAttachment(
        entry_id=entry.id,
        uploader_id=user.id,
        file_name=file.filename or f"file{ext}",
        file_path=rel_path,
        file_size=len(content),
        mime_type=file.content_type or "",
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return ok(
        {"id": att.id, "file_name": att.file_name, "file_size": att.file_size, "mime_type": att.mime_type},
        message="上传成功",
    )


@router.get("/{attachment_id}/download")
def download(
    attachment_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    att = db.get(KbAttachment, attachment_id)
    if att is None or att.is_deleted != 0:
        raise biz_error(E_ATTACHMENT_NOT_FOUND)
    entry = entry_service.get_active(db, att.entry_id)
    entry_service.get_visible_entry(db, entry.id, user)  # 跟随条目权限

    abs_path = UPLOAD_DIR / att.file_path
    if not abs_path.is_file():
        raise biz_error(E_ATTACHMENT_NOT_FOUND)

    from urllib.parse import quote
    from fastapi.responses import FileResponse

    return FileResponse(
        abs_path,
        filename=att.file_name,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(att.file_name)}"},
    )


@router.delete("/{attachment_id}")
def remove(
    attachment_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    att = db.get(KbAttachment, attachment_id)
    if att is None or att.is_deleted != 0:
        raise biz_error(E_ATTACHMENT_NOT_FOUND)
    entry = entry_service.get_active(db, att.entry_id)
    entry_service.check_manage_permission(user, entry)
    att.is_deleted = 1
    db.commit()
    return ok(None, message="删除成功")
