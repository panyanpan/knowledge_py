from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    admin,
    announcements,
    attachments,
    auth,
    categories,
    entries,
    knowledge,
    metadata,
    portal,
    rules,
    svcs,
    tags,
)
from app.core.error_codes import E_FORBIDDEN, E_TOKEN_INVALID
from app.core.exceptions import BizError
from app.core.response import fail

app = FastAPI(title="Knowledge Base API", version="0.2.0", docs_url=None, redoc_url=None)

# Swagger/ReDoc 资源本地化：/docs 不再依赖国外 CDN（离线环境/代理下仍可打开）
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS：前后端分离部署，显式限定来源/方法/头
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(entries.router)
app.include_router(attachments.router)
app.include_router(portal.router)
app.include_router(announcements.router)
app.include_router(metadata.router)
app.include_router(knowledge.router)
app.include_router(rules.router)
app.include_router(svcs.router)


@app.get("/", tags=["system"])
def root():
    return {"code": 0, "message": "Knowledge Base API", "data": {"docs": "/docs", "health": "/health"}}


@app.get("/docs", include_in_schema=False)
def custom_docs():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
def custom_redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/health", tags=["system"])
def health():
    return {"code": 0, "message": "ok", "data": {"status": "up"}}


# ---------- 统一异常处理：全部以 { code, message, data } 返回，不泄露堆栈 ----------


@app.exception_handler(BizError)
async def biz_error_handler(_: Request, exc: BizError):
    return _json_response(exc.status, fail(exc.code, exc.message))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return _json_response(422, fail(400, "参数校验失败", data=exc.errors()))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    # 框架层 HTTP 异常（如 404 路由不存在）映射到统一响应体
    code = {401: E_TOKEN_INVALID[0], 403: E_FORBIDDEN[0]}.get(exc.status_code, exc.status_code)
    return _json_response(exc.status_code, fail(code, str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    # 兜底：不向前端泄露堆栈细节
    return _json_response(500, fail(500, "服务器内部错误"))


def _json_response(status: int, body: dict):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status, content=body)
