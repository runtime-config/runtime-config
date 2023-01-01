import getpass

import pydantic
from aiopg.sa import SAConnection

from runtime_config.config import get_config
from runtime_config.db import close_db, get_db_conn, init_db
from runtime_config.entities.user import NewAdminUser
from runtime_config.services.account.user import create_admin_user

SECRET_FIELDS = ['password']


async def create_admin() -> None:
    config = get_config()
    await init_db(config.db_dsn)
    try:
        async with get_db_conn() as conn:
            await _create_admin(conn)
    finally:
        await close_db()


async def _create_admin(conn: SAConnection) -> None:
    admin_form = None
    while admin_form is None:
        try:
            admin_form = _input_form_value()
        except pydantic.ValidationError as exc:
            print(f'You entered invalid data:\n{exc}\n')

    try:
        await create_admin_user(conn=conn, user=admin_form.dict())
    except Exception as exc:
        print(f'User create failed:\n{exc}')
    else:
        print('User created successful')


def _input_form_value() -> NewAdminUser:
    input_data = {}
    field_names = filter(lambda name: name not in SECRET_FIELDS, NewAdminUser.__fields__.keys())
    promt_template = 'Input {field}: '
    for name in field_names:
        value = input(promt_template.format(field=name)) or None
        input_data[name] = value

    password = getpass.getpass(promt_template.format(field='password'))

    return NewAdminUser(password=password, **input_data)
