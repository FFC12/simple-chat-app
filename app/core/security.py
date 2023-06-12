from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel

from app.core.base import app


class Settings(BaseModel):
    """
    This is a simple setup for FastAPI JWT Auth. Authentiocation is a complex topic and
    this is just one way to implement it. I use it in our projects and it works well.
    To be more secured, needs always more work.
    """
    authjwt_secret_key: str = "secret"
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False


@AuthJWT.load_config
def get_config():
    """
    Load config for FastAPI JWT Auth
    :return:
    """
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    """
    Exception handler for FastAPI JWT Auth
    :param request:
    :param exc:
    :return:
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
