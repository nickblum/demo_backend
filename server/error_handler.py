from fastapi import Request, status
from fastapi.responses import JSONResponse
from server.logger import get_logger

logger = get_logger(__name__)

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"AppException: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else None,
    })
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

def setup_error_handlers(app):
    app.add_exception_handler(AppException, app_exception_handler)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        })
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )