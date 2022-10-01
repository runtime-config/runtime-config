import typing as t
from functools import partial

from fastapi import FastAPI

from runtime_config.config import Config, get_config
from runtime_config.lib.db import close_db, init_db
from runtime_config.logger import init_logger
from runtime_config.web.routes import init_routes


def init_hooks(application: FastAPI, config: Config) -> None:
    application.on_event('startup')(partial(init_db, dsn=config.db_dsn))
    application.on_event('shutdown')(close_db)


def app_factory(app_hooks: t.Callable[[FastAPI, Config], None] = init_hooks) -> FastAPI:
    config = get_config()
    init_logger(log_mode=config.log_mode.value, log_level=config.log_level)

    application = FastAPI(title='runtime-config')
    app_hooks(application, config)
    init_routes(application)
    return application
