from databases import Database

from runtime_config.lib.exception import ServiceInstanceNotFound

_inst: dict[str, Database] = {}


def get_db() -> Database:
    try:
        return _inst['db']
    except KeyError:
        raise ServiceInstanceNotFound('db')


def set_db(db: Database) -> None:
    _inst['db'] = db


async def init_db(dsn: str, force_rollback: bool = False) -> Database:
    db = Database(url=dsn, force_rollback=force_rollback)
    await db.connect()
    set_db(db)
    return db


async def close_db() -> None:
    try:
        db = get_db()
    except ServiceInstanceNotFound:
        pass
    else:
        await db.disconnect()
