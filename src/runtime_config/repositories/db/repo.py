import typing as t

from aiopg.sa import SAConnection
from sqlalchemy import delete, desc, insert, select, update

from runtime_config.models import Setting, SettingHistory
from runtime_config.repositories.db.entities import SettingData, SettingHistoryData


async def delete_setting(conn: SAConnection, setting_id: int) -> bool:
    query = delete(Setting).where(Setting.id == setting_id).returning(Setting.id)
    deleted_row_id = await (await conn.execute(query)).fetchone()
    return bool(deleted_row_id)


async def create_new_setting(conn: SAConnection, values: dict[str, t.Any]) -> SettingData | None:
    query = insert(Setting).values(values).returning(Setting)

    row = await (await conn.execute(query)).fetchone()

    created_setting = None
    if row is not None:
        created_setting = SettingData(**row)

    return created_setting


async def edit_setting(conn: SAConnection, setting_id: int, values: dict[str, t.Any]) -> SettingData | None:
    query = update(Setting).where(Setting.id == setting_id).values(values).returning(Setting)
    row = await (await conn.execute(query)).fetchone()
    return SettingData(**row) if row else None


async def get_setting(
    conn: SAConnection, setting_id: int, include_history: bool = False
) -> tuple[SettingData | None, list[SettingHistoryData]]:
    query = select(Setting).where(Setting.id == setting_id)

    row = await (await conn.execute(query)).fetchone()
    found_setting = None
    if row is not None:
        found_setting = SettingData(**row)

    history_rows = []
    if include_history and found_setting:
        query_history = (
            select(SettingHistory)
            .where(
                SettingHistory.name == found_setting.name,
                SettingHistory.service_name == found_setting.service_name,
            )
            .order_by(desc(SettingHistory.updated_at))
        )
        history_rows = [SettingHistoryData(**row) async for row in conn.execute(query_history)]

    return found_setting, history_rows


async def search_settings(
    conn: SAConnection, name: str | None, service_name: str | None, offset: int = 0, limit: int = 30
) -> t.AsyncIterable[SettingData]:
    query = select(Setting).offset(offset).limit(limit)

    if name is not None:
        query = query.where(Setting.name.like(f'%{name}%'))

    if service_name is not None:
        query = query.where(Setting.service_name == service_name)

    async for row in conn.execute(query):
        yield SettingData(**row)


async def get_service_settings(
    conn: SAConnection, service_name: str, offset: int = 0, limit: int | None = None
) -> t.AsyncIterable[SettingData]:
    query = select(Setting).where(Setting.service_name == service_name).offset(offset)
    if limit:
        query = query.limit(limit)

    async for row in conn.execute(query):
        yield SettingData(**row)
