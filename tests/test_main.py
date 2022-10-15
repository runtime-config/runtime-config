from fastapi import FastAPI
from pytest_mock import MockerFixture

from runtime_config.main import init_hooks


async def test_init_hooks(mocker: MockerFixture):
    # arrange
    init_db_mock = mocker.patch('runtime_config.main.init_db')
    close_db_mock = mocker.patch('runtime_config.main.close_db')
    app_mock = mocker.MagicMock(FastAPI)
    config_mock = mocker.Mock()

    # act
    init_hooks(app_mock, config_mock)
    for call in app_mock.on_event().call_args_list:
        fn = call[0][0]
        await fn(app_mock)

    # assert
    init_db_mock.assert_called_with(app_mock, dsn=config_mock.db_dsn)
    close_db_mock.assert_called_with(app_mock)
