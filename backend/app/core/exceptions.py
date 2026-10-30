class BizError(Exception):
    """业务异常：由全局 handler 转为统一响应体。"""

    def __init__(self, code: int, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)
