import typing as t

from sqlalchemy import select

from runtime_config.lib.db import get_db
from runtime_config.models import Setting


async def get_service_settings(service_name: str) -> t.AsyncIterable[dict[str, t.Any]]:
    db = get_db()
    query = select(
        Setting.name,
        Setting.value,
        Setting.value_type,
        Setting.disable,
    ).where(Setting.service_name == service_name)
    async for row in db.iterate(query):
        yield t.cast(dict[str, t.Any], row)
