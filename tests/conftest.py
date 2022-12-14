import typing as t

import pytest
from aiopg.sa import Engine, SAConnection
from fastapi import FastAPI
from httpx import AsyncClient

from runtime_config.config import Config, get_config
from runtime_config.lib.db import close_db, get_db_conn, init_db
from runtime_config.lib.db_utils import apply_migrations, create_db, drop_db
from runtime_config.main import app_factory
from tests.fixtures import *  # noqa: F403, F401


@pytest.fixture(scope='session', name='config', autouse=True)
def config_fixture() -> Config:
    config = get_config()
    config.db_name = f'{config.db_name}_test'
    return config


@pytest.fixture(scope='session', autouse=True)
def init_test_db(config: Config) -> t.Generator[None, None, None]:
    test_db_name = config.db_dsn.path[1:]
    dns = str(config.db_dsn).replace(test_db_name, 'postgres')

    create_db(dsn=dns, db_name=test_db_name)
    apply_migrations(config.project_dir)

    yield

    drop_db(dsn=dns, db_name=test_db_name)


@pytest.fixture(name='db')
async def db_fixture(config: Config) -> t.AsyncGenerator[Engine, None]:
    db = await init_db(dsn=config.db_dsn)
    yield db
    await close_db()


@pytest.fixture(name='db_conn')
async def db_conn_fixture(db: Engine) -> t.AsyncGenerator[SAConnection, None]:
    async with db.acquire() as conn:
        tx = await conn.begin()
        yield conn
        await tx.rollback()


@pytest.fixture(name='app')
async def app_fixture(config: Config, db_conn: SAConnection) -> t.AsyncGenerator[FastAPI, None]:
    app = app_factory(app_hooks=lambda *args, **kwargs: None)
    app.dependency_overrides[get_db_conn] = lambda: db_conn
    yield app


@pytest.fixture
async def async_client(app: FastAPI) -> t.AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
