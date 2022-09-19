import typing as t

from sqlalchemy import delete, desc, insert, select, update
from sqlalchemy.sql.expression import literal_column

from runtime_config.lib.db import get_db
from runtime_config.models import Setting, SettingHistory
from runtime_config.repositories.db.entities import (
    SearchParams,
    SettingData,
    SettingHistoryData,
)


async def delete_setting(setting_id: int) -> bool:
    db = get_db()
    query = delete(Setting).where(Setting.id == setting_id).returning(Setting.id)
    deleted_row_id = await db.fetch_one(query)
    return bool(deleted_row_id)


async def create_new_setting(values: dict[str, t.Any]) -> SettingData | None:
    db = get_db()
    query = (
        insert(Setting)
        .values(values)
        .returning(
            Setting.id,
            Setting.name,
            Setting.value,
            Setting.value_type,
            Setting.disable,
            Setting.service_name,
            Setting.created_by_db_user,
            Setting.updated_at,
        )
    )
    row = await db.fetch_one(query)

    created_setting = None
    if row is not None:
        created_setting = SettingData(**row)  # type: ignore[arg-type]

    return created_setting


async def edit_setting(setting_id: int, values: dict[str, t.Any]) -> SettingData | None:
    db = get_db()
    query = update(Setting).where(Setting.id == setting_id).values(values).returning(literal_column('*'))
    row = await db.fetch_one(query)
    return SettingData(**row) if row else None  # type: ignore[arg-type]


async def get_setting(
    setting_id: int, include_history: bool = False
) -> tuple[SettingData | None, list[SettingHistoryData]]:
    db = get_db()
    query = select(
        Setting.id,
        Setting.name,
        Setting.value,
        Setting.value_type,
        Setting.disable,
        Setting.service_name,
        Setting.created_by_db_user,
        Setting.updated_at,
    ).where(Setting.id == setting_id)

    row = await db.fetch_one(query)
    found_setting = None
    if row is not None:
        found_setting = SettingData(**row)  # type: ignore[arg-type]

    history_rows = []
    if include_history and found_setting:
        query_history = (
            select(
                SettingHistory.id,
                SettingHistory.name,
                SettingHistory.value,
                SettingHistory.value_type,
                SettingHistory.disable,
                SettingHistory.service_name,
                SettingHistory.created_by_db_user,
                SettingHistory.updated_at,
                SettingHistory.is_deleted,
                SettingHistory.deleted_by_db_user,
            )
            .where(
                SettingHistory.name == found_setting.name, SettingHistory.service_name == found_setting.service_name
            )
            .order_by(desc(SettingHistory.updated_at))
        )
        history_rows = [SettingHistoryData(**row) async for row in db.iterate(query_history)]

    return found_setting, history_rows


async def search_settings(
    search_params: SearchParams, offset: int = 0, limit: int = 30
) -> t.AsyncIterable[SettingData]:
    db = get_db()
    query = (
        select(
            Setting.id,
            Setting.name,
            Setting.value,
            Setting.value_type,
            Setting.disable,
            Setting.service_name,
            Setting.created_by_db_user,
            Setting.updated_at,
        )
        .offset(offset)
        .limit(limit)
    )

    if 'name' in search_params:
        query = query.where(Setting.name.like(f'%{search_params["name"]}%'))

    if 'service_name' in search_params:
        query = query.where(Setting.service_name == search_params['service_name'])

    async for row in db.iterate(query):
        yield SettingData(**row)


async def get_service_settings(
    service_name: str, offset: int = 0, limit: int | None = None
) -> t.AsyncIterable[SettingData]:
    db = get_db()
    query = (
        select(
            Setting.id,
            Setting.name,
            Setting.value,
            Setting.value_type,
            Setting.disable,
            Setting.service_name,
            Setting.created_by_db_user,
            Setting.updated_at,
        )
        .where(Setting.service_name == service_name)
        .offset(offset)
    )
    if limit:
        query = query.limit(limit)

    async for row in db.iterate(query):
        yield SettingData(**row)
