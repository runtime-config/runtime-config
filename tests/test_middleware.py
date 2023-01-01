from fastapi import Request
from pytest_mock import MockerFixture

from runtime_config.middleware import db_conn_middleware


async def test_db_conn_middleware(mocker: MockerFixture):
    # arrange
    request = mocker.MagicMock(Request)
    next_call = mocker.AsyncMock()
    db_conn = mocker.Mock()

    get_db_conn_mock = mocker.patch('runtime_config.middleware.get_db_conn')
    get_db_conn_mock.return_value.__aenter__.return_value = db_conn

    # act
    await db_conn_middleware(request, next_call)

    # assert
    assert request.state.db_conn == db_conn
    assert next_call.call_args.args[0] == request
