import pytest
from aiopg.sa import Engine
from pytest_mock import MockerFixture

import runtime_config.lib.db as db_module
from runtime_config.lib.db import close_db, get_db, get_db_conn
from runtime_config.lib.exception import ServiceInstanceNotFound


def test_get_db(mocker: MockerFixture):
    # arrange
    db_mock = mocker.Mock()
    mocker.patch.dict(db_module._inst, {'db': db_mock})

    # act
    db = get_db()

    # arrange
    assert db == db_mock


async def test_get_db_conn(db_mock):
    # act
    conn = await anext(get_db_conn())

    # arrange
    assert conn == await db_mock.acquire().__aenter__()


def test_get_db__db_engine_instance_was_not_created__raise_exception(mocker: MockerFixture):
    # arrange
    mocker.patch.dict(db_module._inst, {}, clear=True)

    # act && arrange
    with pytest.raises(ServiceInstanceNotFound):
        get_db()


async def test_close_db(db_mock):
    # act
    await close_db()

    # assert
    assert db_mock.close.call_count == 1
    assert db_mock.wait_closed.call_count == 1


async def test_close_db__db_engine_instance_was_not_created__success(mocker: MockerFixture):
    # arrange
    mocker.patch('runtime_config.lib.db.get_db', side_effect=ServiceInstanceNotFound('db'))

    # act && assert
    await close_db()


@pytest.fixture(name='db_mock')
def db_mock_fixture(mocker: MockerFixture):
    db_mock = mocker.MagicMock(spec=Engine)
    mocker.patch.dict(db_module._inst, {'db': db_mock})
    return db_mock
