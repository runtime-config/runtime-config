import typing as t

import pytest
from aiopg.sa import Engine, SAConnection
from fastapi import FastAPI
from httpx import AsyncClient

from runtime_config.config import Config, get_config
from runtime_config.db import close_db, init_db
from runtime_config.enums.user import UserRole
from runtime_config.lib.db_utils import apply_migrations, create_db, drop_db
from runtime_config.main import app_factory, get_middleware
from runtime_config.middleware import db_conn_middleware
from runtime_config.repositories.db.repo import create_user
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
    middleware = mock_middleware(get_middleware(), db_conn)
    app = app_factory(app_hooks=lambda *args, **kwargs: None, middleware=middleware)
    yield app


@pytest.fixture
async def async_client(app: FastAPI, admin_user) -> t.AsyncGenerator[AsyncClient, None]:
    token = app.state.jwt_token_service._create_access_token(admin_user)
    async with AsyncClient(app=app, base_url="http://test", headers={'Authorization': f'Bearer {token}'}) as client:
        yield client


@pytest.fixture(name='admin_user')
async def admin_user_fixture(db_conn: SAConnection):
    return await create_user(
        conn=db_conn,
        values={
            'username': 'alex',
            'email': 'alex@mail.ru',
            'password': 'qwerty',
            'role': UserRole.admin,
            'is_active': True,
        },
    )


def get_db_conn_middleware_mock(db_conn):
    async def middleware(request, call_next):
        request.state.db_conn = db_conn
        return await call_next(request)

    return middleware


def mock_middleware(original_middleware, db_conn):
    mapping = {db_conn_middleware: get_db_conn_middleware_mock(db_conn)}
    return [mapping.get(func, func) for func in original_middleware]
