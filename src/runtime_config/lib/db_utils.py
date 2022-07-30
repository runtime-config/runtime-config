import os
from logging import getLogger
from pathlib import Path

from alembic.config import main as alembic_commands
from sqlalchemy import create_engine

from runtime_config.lib.logger import root_logger_cleaner

logger = getLogger(__name__)


def create_db(dsn: str, db_name: str) -> None:
    engine = create_engine(dsn, isolation_level='AUTOCOMMIT')

    with engine.connect() as conn:
        conn.execute(f'DROP DATABASE IF EXISTS {db_name}')
        conn.execute(f'CREATE DATABASE {db_name}')


def drop_db(dsn: str, db_name: str) -> None:
    engine = create_engine(dsn, isolation_level='AUTOCOMMIT')

    with engine.connect() as conn:
        # terminate all connections to be able to drop database
        conn.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid();
            """
        )
        conn.execute(f'DROP DATABASE IF EXISTS {db_name}')


def apply_migrations(root_dir: Path) -> None:
    """
    Applies all migrations to the current database
    :param root_dir: the root directory of the project (the directory in which the
    folder containing the migrations is located)
    """
    cwd = os.getcwd()
    os.chdir(root_dir)
    logger_cleaner = root_logger_cleaner()
    next(logger_cleaner)

    try:
        alembic_commands(
            argv=(
                '--raiseerr',
                'upgrade',
                'head',
            )
        )
    except Exception:
        next(logger_cleaner)
        logger.warning(
            'An unexpected error occurred while trying to apply migrations',
            exc_info=True,
        )
        raise
    finally:
        os.chdir(cwd)

    next(logger_cleaner)
