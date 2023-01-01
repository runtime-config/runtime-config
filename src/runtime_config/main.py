import typing as t
from functools import partial

from fastapi import FastAPI

from runtime_config.config import Config, get_config
from runtime_config.db import close_db, init_db
from runtime_config.logger import init_logger
from runtime_config.middleware import (
    MIDDLEWARE_TYPE,
    current_user_middleware,
    db_conn_middleware,
)
from runtime_config.services.account.security import JwtTokenService
from runtime_config.web.routes import init_routes


def init_hooks(app: FastAPI, config: Config) -> None:
    app.on_event('startup')(partial(init_db, dsn=config.db_dsn))
    app.on_event('shutdown')(close_db)


def get_middleware() -> list[MIDDLEWARE_TYPE]:
    return [current_user_middleware, db_conn_middleware]


def app_factory(
    app_hooks: t.Callable[[FastAPI, Config], None] = init_hooks, middleware: list[MIDDLEWARE_TYPE] = None
) -> FastAPI:
    config = get_config()
    init_logger(log_mode=config.log_mode.value, log_level=config.log_level)

    app = FastAPI(title='runtime-config')

    for func in middleware or get_middleware():
        app.middleware('http')(func)

    app.state.jwt_token_service = JwtTokenService(
        secret_key=config.secret_key,
        access_token_expire_time=config.jwt_access_token_expire_time,
        refresh_token_expire_time=config.jwt_refresh_token_expire_time,
        algorithm=config.jwt_token_algorithm,
    )

    app_hooks(app, config)
    init_routes(app)

    return app
