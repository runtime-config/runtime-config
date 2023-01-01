import typing as t

from aiopg.sa import SAConnection
from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from structlog import get_logger

from runtime_config.db import get_db_conn
from runtime_config.services.account.security import JwtTokenService

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

CALL_NEXT_TYPE = t.Callable[[Request], t.Awaitable[Response]]
MIDDLEWARE_TYPE = t.Callable[[Request, t.Callable[[Request], t.Awaitable[Response]]], t.Awaitable[Response]]


async def db_conn_middleware(request: Request, call_next: CALL_NEXT_TYPE) -> Response:
    async with get_db_conn() as db_conn:
        request.state.db_conn = db_conn
        return await call_next(request)


async def current_user_middleware(request: Request, call_next: CALL_NEXT_TYPE) -> Response:
    db_conn: SAConnection = request.state.db_conn
    jwt_token_service: JwtTokenService = request.app.state.jwt_token_service

    token = None
    try:
        token = await oauth2_scheme(request)
    except HTTPException:
        pass

    if token:
        request.state.user = await jwt_token_service.get_user_from_access_token(db_conn=db_conn, token=token)
    else:
        request.state.user = None
        logger.info('Authorization token was not found in request')

    return await call_next(request)
