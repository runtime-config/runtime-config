import typing as t

from aiopg.sa import SAConnection
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from runtime_config.models import Setting


async def create_setting(conn: SAConnection, value: dict[str, t.Any]) -> dict[str, t.Any]:
    query = insert(Setting).values(value).returning('*')
    return dict(await (await conn.execute(query)).fetchone())


async def count_settings(conn: SAConnection) -> int:
    query = select(func.count()).select_from(select(Setting))
    return (await (await conn.execute(query)).fetchone())[0]


async def get_all_settings(conn: SAConnection) -> list[dict[str, t.Any]]:
    query = select(Setting)
    return [dict(row) for row in await (await conn.execute(query)).fetchall()]
