import typing as t

import psycopg2.errors
from aiopg.sa import SAConnection

from runtime_config.enums.user import UserRole
from runtime_config.repositories.db.entities import User
from runtime_config.repositories.db.repo import create_user as create_user_in_db
from runtime_config.services.account.security import get_password_hash


async def create_admin_user(conn: SAConnection, values: dict[str, t.Any]) -> None:
    data: dict[str, t.Any] = {'is_active': True, 'role': UserRole.admin, **values}
    await create_new_user(conn=conn, values=data)


async def create_simple_user(conn: SAConnection, values: dict[str, t.Any]) -> None:
    data: dict[str, t.Any] = {'is_active': False, 'role': UserRole.user, **values}
    await create_new_user(conn=conn, values=data)


async def create_new_user(conn: SAConnection, values: dict[str, t.Any]) -> User:
    values['password'] = get_password_hash(values['password'])
    try:
        return await create_user_in_db(conn=conn, values=values)
    except psycopg2.errors.UniqueViolation as exc:
        pg_error = exc.diag.message_detail
        if pg_error:
            field = pg_error[pg_error.find('(') + 1 : pg_error.find(')')]
            value = pg_error[pg_error.rfind('(') + 1 : pg_error.rfind(')')]
            msg = f'User with {field}={value} already exists'
        else:
            msg = 'This is user already exists'
        raise ValueError(msg)
