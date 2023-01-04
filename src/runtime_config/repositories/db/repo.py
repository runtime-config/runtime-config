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


async def delete_settings(conn: SAConnection, setting_ids: list[int]) -> list[int]:
    query = delete(Setting).where(Setting.id.in_(setting_ids)).returning(Setting.id)
    deleted_rows_id = await (await conn.execute(query)).fetchall()
    return [row[0] for row in deleted_rows_id]


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


async def create_user(conn: SAConnection, values: dict[str, t.Any]) -> User:
    query = insert(UserModel).values(values).returning(UserModel)
    row = await (await conn.execute(query)).fetchone()
    return User(**row)


async def get_user(conn: SAConnection, user_id: int | None = None, username: str = None) -> User | None:
    users = await get_users(
        conn=conn, user_ids=[user_id] if user_id else None, usernames=[username] if username else None
    )
    return users[0] if users else None


async def get_users(conn: SAConnection, user_ids: list[int] | None = None, usernames: list[str] = None) -> list[User]:
    assert any((user_ids, usernames)), 'user_ids or usernames must be not none'
    query = select(UserModel)
    if user_ids:
        query = query.where(UserModel.id.in_(user_ids))
    else:
        query = query.where(UserModel.username.in_(usernames))
    users = await (await conn.execute(query)).fetchall()
    return [User(**usr) for usr in users]


async def delete_users(conn: SAConnection, user_ids: list[int]) -> list[int]:
    query = delete(UserModel).where(UserModel.id.in_(user_ids)).returning(UserModel.id)
    deleted_rows_id = await (await conn.execute(query)).fetchall()
    return [row[0] for row in deleted_rows_id]


async def edit_user(conn: SAConnection, user_id: int, values: dict[str, t.Any]) -> User | None:
    query = update(UserModel).where(UserModel.id == user_id).values(values).returning(UserModel)
    row = await (await conn.execute(query)).fetchone()
    return User(**row) if row else None


async def search_user(
    conn: SAConnection, values: dict[str, t.Any | None], offset: int = 0, limit: int = 30
) -> t.AsyncIterable[User]:
    query = select(UserModel).offset(offset).limit(limit)

    for field, val in values.items():
        if val is not None:
            query = query.where(getattr(UserModel, field) == val)

    async for row in conn.execute(query):
        yield User(**row)


async def get_all_users(conn: SAConnection, offset: int = 0, limit: int | None = None) -> t.AsyncIterable[User]:
    query = select(UserModel).offset(offset)
    if limit:
        query = query.limit(limit)

    async for row in conn.execute(query):
        yield User(**row)


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
