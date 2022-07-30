import pytest
from databases import Database
from psycopg2.errors import UniqueViolation  # noqa
from sqlalchemy import func, select, update
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
    values = {**setting_data, 'user_name': 'not_valid_username'}
    query = insert(Setting).values(values)
    expected_user_name = config.db_user

    # act
    await db.execute(query)

    # assert
    all_settings = await get_all_settings(db)
    assert len(all_settings) == 1
    assert all_settings[0] == {
        **setting_data,
        'id': 1,
        'user_name': expected_user_name,
        'updated_at': mocker.ANY,
    }


async def test_setting__change_row_in_table__historical_record_created(
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
        'id': 1,
        'setting_id': created_setting['id'],
        'value_type': ValueType(created_setting['value_type']),
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
