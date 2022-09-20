import pytest
from databases import Database
from psycopg2.errors import UniqueViolation  # noqa
from pytest_mock import MockerFixture
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from runtime_config.enums.settings import ValueType
from runtime_config.models import Setting, SettingHistory
from tests.db_utils import create_setting, get_all_settings


async def test_setting__user_field_is_filled_with_non_existing_user__valid_value_inserted(
    mocker,
    config,
    db: Database,
    setting_data,
) -> None:
    # arrange
    values = {**setting_data, 'created_by_db_user': 'not_valid_username'}
    query = insert(Setting).values(values)
    expected_created_by_db_user = config.db_user

    # act
    await db.execute(query)

    # assert
    all_settings = await get_all_settings(db)
    assert len(all_settings) == 1
    assert all_settings[0] == {
        **setting_data,
        'id': 1,
        'created_by_db_user': expected_created_by_db_user,
        'updated_at': mocker.ANY,
    }


async def test_setting__update_row__historical_record_created(
    mocker: MockerFixture,
    db: Database,
    setting_data,
):
    # arrange
    created_setting = await create_setting(db, setting_data)

    # act
    count_history_before = await db.fetch_one(select(func.count()).select_from(SettingHistory))
    await db.execute(update(Setting).where(Setting.id == created_setting['id']).values(value=100))
    history_records = await db.fetch_all(select(SettingHistory))

    # assert
    assert count_history_before[0] == 0
    assert len(history_records) == 1
    assert dict(history_records[0]) == {
        **created_setting,
        'id': mocker.ANY,
        'value_type': ValueType(created_setting['value_type']),
        'is_deleted': False,
        'deleted_by_db_user': None,
    }


async def test_setting__delete_row__row_moved_to_setting_history_table(
    mocker: MockerFixture,
    db: Database,
    setting_data,
):
    # arrange
    created_setting = await create_setting(db, setting_data)

    # act
    count_history_before = await db.fetch_one(select(func.count()).select_from(SettingHistory))
    await db.execute(delete(Setting).where(Setting.id == created_setting['id']))
    history_records = await db.fetch_all(select(SettingHistory))

    # assert
    assert count_history_before[0] == 0
    assert len(history_records) == 1
    assert dict(history_records[0]) == {
        **created_setting,
        'id': mocker.ANY,
        'value_type': ValueType(created_setting['value_type']),
        'is_deleted': True,
        'deleted_by_db_user': 'admin',
    }


async def test_setting__create_two_settings_with_same_name_in_one_service__historical_record_created__return_error(
    db: Database,
    setting_data,
):
    # arrange
    expected_error = 'duplicate key value violates unique constraint "unique_setting_name_per_service"'
    await create_setting(db, setting_data)
    setting_data2 = {
        **setting_data,
        'value': '1111',
    }

    # act
    with pytest.raises(UniqueViolation) as exc:
        await create_setting(db, setting_data2)

    # assert
    assert expected_error in str(exc)
