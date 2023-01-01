import contextlib
import typing as t

from aiopg.sa import Engine, SAConnection, create_engine
from pydantic.networks import PostgresDsn
from structlog import get_logger

from runtime_config.exception import ServiceInstanceNotFound

logger = get_logger(__name__)

_inst: dict[str, Engine] = {}


def get_db() -> Engine:
    try:
        return _inst['db']
    except KeyError:
        raise ServiceInstanceNotFound('db')


@contextlib.asynccontextmanager
async def get_db_conn() -> t.AsyncIterator[SAConnection]:
    async with get_db().acquire() as conn:
        yield conn


def set_db(db: Engine) -> None:
    _inst['db'] = db


async def init_db(dsn: PostgresDsn) -> Engine:
    db = await create_engine(dsn=dsn)
    set_db(db)
    logger.info('Database connection pool initialized successfully')
    return db


async def close_db() -> None:
    try:
        db = get_db()
    except ServiceInstanceNotFound:
        logger.warning('Connection pool has not been initialized, cannot close connection pool')
    else:
        db.close()
        await db.wait_closed()
        logger.info('Database connection pool closed')
