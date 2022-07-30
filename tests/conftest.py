from typing import AsyncGenerator, Generator

import pytest
from databases import Database
from fastapi import FastAPI
from httpx import AsyncClient

from runtime_config.config import Config, get_config
from runtime_config.lib.db import close_db, get_db, init_db
from runtime_config.lib.db_utils import apply_migrations, create_db, drop_db
from runtime_config.main import app_factory
from tests.fixtures import *  # noqa: F403, F401


@pytest.fixture(scope='session', name='config', autouse=True)
def config_fixture() -> Config:
    config = get_config()
    config.db_name = f'{config.db_name}_test'
    return config


@pytest.fixture(scope='session', autouse=True)
def init_test_db(config: Config) -> Generator[None, None, None]:
    test_db_name = config.db_dsn.path.replace('/', '')
    dns = str(config.db_dsn).replace(test_db_name, 'postgres').replace('postgresql+aiopg', 'postgresql')

    create_db(dsn=dns, db_name=test_db_name)
    apply_migrations(config.project_dir)

    yield

    drop_db(dsn=dns, db_name=test_db_name)


@pytest.fixture(name='app')
async def app_fixture(config: Config) -> AsyncGenerator[FastAPI, None]:
    application = app_factory(app_hooks=lambda *args, **kwargs: None)
    await init_db(dsn=config.db_dsn, force_rollback=True)

    yield application

    await close_db()


@pytest.fixture
async def db(app: FastAPI) -> Database:
    return get_db()


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
