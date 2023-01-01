import typing as t

from fastapi import Request, Response

from runtime_config.db import get_db_conn

CALL_NEXT_TYPE = t.Callable[[Request], t.Awaitable[Response]]
MIDDLEWARE_TYPE = t.Callable[[Request, t.Callable[[Request], t.Awaitable[Response]]], t.Awaitable[Response]]


async def db_conn_middleware(request: Request, call_next: CALL_NEXT_TYPE) -> Response:
    async with get_db_conn() as db_conn:
        request.state.db_conn = db_conn
        return await call_next(request)
