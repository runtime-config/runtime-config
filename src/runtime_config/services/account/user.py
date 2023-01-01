import typing as t

from aiopg.sa import SAConnection

from runtime_config.enums.user import UserRole
from runtime_config.repositories.db.repo import create_user
from runtime_config.services.account.security import get_password_hash


async def create_admin_user(conn: SAConnection, user: dict[str, t.Any]) -> None:
    data: dict[str, t.Any] = {'is_active': True, 'role': UserRole.admin, **user}
    data['password'] = get_password_hash(data['password'])
    await create_user(conn=conn, data=data)
