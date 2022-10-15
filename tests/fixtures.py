import pytest

from runtime_config.enums.settings import ValueType

__all__ = ['setting_data_fixture']


@pytest.fixture(name='setting_data')
def setting_data_fixture(config):
    return {
        'name': 'timeout',
        'value': '10',
        'value_type': ValueType.int,
        'disabled': False,
        'service_name': 'service-name',
        'created_by_db_user': config.db_user,
    }
