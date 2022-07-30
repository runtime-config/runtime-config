import typing as t

from databases import Database
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from runtime_config.models import Setting


async def create_setting(db: Database, value) -> dict[str, t.Any]:
    query = insert(Setting).values(value).returning('*')
    return dict(await db.fetch_one(query))


async def get_all_settings(db: Database) -> list[dict[str, t.Any]]:
    query = select(Setting)
    return [dict(row) for row in await db.fetch_all(query)]
