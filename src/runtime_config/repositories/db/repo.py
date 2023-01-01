import typing as t

from aiopg.sa import SAConnection
from sqlalchemy import delete, desc, insert, select, update

from runtime_config.enums.token import TokenType
from runtime_config.models import Setting, SettingHistory
from runtime_config.models import Token as TokenModel
from runtime_config.models import User as UserModel
from runtime_config.repositories.db.entities import (
    SettingData,
    SettingHistoryData,
    Token,
    User,
)


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


async def create_user(conn: SAConnection, data: dict[str, t.Any]) -> User:
    query = insert(UserModel).values(data).returning(UserModel)
    row = await (await conn.execute(query)).fetchone()
    return User(**row)


async def get_user(conn: SAConnection, username: str) -> User | None:
    query = select(UserModel).where(UserModel.username == username)
    user = await (await conn.execute(query)).fetchone()
    return User(**user) if user else None


async def get_user_refresh_token(conn: SAConnection, refresh_token: str, user_id: int) -> Token | None:
    query = select(TokenModel).where(
        TokenModel.user_id == user_id, TokenModel.token == refresh_token, TokenModel.type == TokenType.refresh
    )
    token = await (await conn.execute(query)).fetchone()
    return Token(**token) if token else None


async def delete_user_refresh_token(conn: SAConnection, user_id: int) -> None:
    await conn.execute(delete(TokenModel).where(TokenModel.user_id == user_id))


async def update_refresh_token(conn: SAConnection, new_token: str, user_id: int) -> None:
    await delete_user_refresh_token(conn=conn, user_id=user_id)
    await conn.execute(insert(TokenModel).values({'user_id': user_id, 'token': new_token, 'type': TokenType.refresh}))
