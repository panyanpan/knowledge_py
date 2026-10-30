from app.core.exceptions import BizError

# 业务错误码约定：0=成功；1xxx=认证/用户域；4xx=参数校验；500=服务器错误
E_USERNAME_OR_EMAIL_TAKEN = (1001, "用户名或邮箱已被注册", 409)
E_BAD_CREDENTIALS = (1002, "用户名或密码错误", 401)
E_TOKEN_INVALID = (1003, "Token 无效或已过期", 401)
E_FORBIDDEN = (1004, "权限不足", 403)
E_ACCOUNT_DISABLED = (1005, "账号已被禁用", 403)
E_TOKEN_TYPE_MISMATCH = (1006, "Token 类型不匹配", 401)


def biz_error(spec: tuple[int, str, int]) -> BizError:
    code, message, status = spec
    return BizError(code=code, message=message, status=status)
