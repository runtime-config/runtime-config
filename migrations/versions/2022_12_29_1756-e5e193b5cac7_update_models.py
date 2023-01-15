"""create models user, token and service_name
table setting and setting_history normalized
add field setting.created_by_user_id
add default value for setting.updated_at
drop fields setting.created_by_db_user, setting_history.created_by_db_user,
     setting_history.deleted_by_db_user
drop all triggers

Revision ID: e5e193b5cac7
Revises: 54e01496163a
Create Date: 2022-12-29 17:56:42.113256

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = 'e5e193b5cac7'
down_revision = '54e01496163a'
branch_labels = None
depends_on = None


bind = op.get_bind()
meta = sa.MetaData(bind=op.get_bind())
db_session = orm.Session(bind=bind)


def create_services():
    setting_table = sa.Table('setting', meta, autoload=True)
    service_name_table = sa.Table('service_name', meta, autoload=True)

    service_names = [row.service_name for row in db_session.query(setting_table).all()]
    created_services = {}
    if service_names:
        query = (
            sa.insert(service_name_table)
            .values([{'name': name} for name in service_names])
            .returning(service_name_table)
        )
        created_services = {row.id: row.name for row in db_session.execute(query).all()}

    return created_services


def replace_service_name_to_service_id(created_services, target_table):
    for service_id, service_name in created_services.items():
        query = (
            sa.update(target_table)
            .where(target_table.c.service_name == service_name)
            .values({'service_name': service_id})
        )
        db_session.execute(query)


def replace_service_id_to_service_name(target_table):
    service_name_table = sa.Table('service_name', meta, autoload=True)

    service_names = {row.id: row.name for row in db_session.query(service_name_table).all()}

    for service_id, service_name in service_names.items():
        query = (
            sa.update(target_table)
            .where(target_table.c.service_name_id == str(service_id))
            .values({'service_name_id': service_name})
        )
        db_session.execute(query)


def upgrade() -> None:
    op.execute('DROP TRIGGER trigger_create_history_entry_for_setting ON setting;')
    op.execute('DROP TRIGGER trigger_fill_user_in_setting_row ON setting;')
    op.execute('DROP FUNCTION create_history_entry_for_setting;')
    op.execute('DROP FUNCTION fill_user_in_setting_row;')

    op.create_table(
        'service_name',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=True),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password', sa.Text(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_table(
        'token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('refresh', name='tokentype'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    created_services = create_services()
    replace_service_name_to_service_id(
        created_services=created_services, target_table=sa.Table('setting', meta, autoload=True)
    )
    op.alter_column(
        'setting', 'service_name', type_=sa.Integer(), postgresql_using='service_name::integer'
    )
    op.alter_column(
        'setting', column_name='service_name', new_column_name='service_name_id', nullable=False
    )
    op.drop_constraint('unique_setting_name_per_service', 'setting', type_='unique')
    op.create_unique_constraint(
        'unique_setting_name_per_service', 'setting', ['name', 'service_name_id']
    )
    op.create_foreign_key(None, 'setting', 'service_name', ['service_name_id'], ['id'])

    op.drop_column('setting', 'created_by_db_user')

    op.add_column('setting', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'setting', 'user', ['created_by_user_id'], ['id'])

    op.alter_column('setting', 'updated_at', server_default=sa.text('now()'))

    replace_service_name_to_service_id(
        created_services=created_services,
        target_table=sa.Table('setting_history', meta, autoload=True),
    )
    op.alter_column(
        'setting_history',
        'service_name',
        type_=sa.Integer(),
        postgresql_using='service_name::integer',
    )
    op.alter_column(
        'setting_history',
        column_name='service_name',
        new_column_name='service_name_id',
        nullable=False,
    )
    op.create_foreign_key(None, 'setting_history', 'service_name', ['service_name_id'], ['id'])

    op.drop_column('setting_history', 'created_by_db_user')
    op.drop_column('setting_history', 'deleted_by_db_user')

    op.add_column('setting_history', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.add_column('setting_history', sa.Column('deleted_by_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'setting_history', 'user', ['created_by_user_id'], ['id'])
    op.create_foreign_key(None, 'setting_history', 'user', ['deleted_by_user_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('unique_setting_name_per_service', 'setting', type_='unique')
    op.drop_constraint('setting_service_name_id_fkey', 'setting', type_='foreignkey')
    op.alter_column('setting', 'service_name_id', type_=sa.Text())
    replace_service_id_to_service_name(sa.Table('setting', meta, autoload=True))
    op.alter_column('setting', column_name='service_name_id', new_column_name='service_name')
    op.create_unique_constraint(
        'unique_setting_name_per_service', 'setting', ['name', 'service_name']
    )

    op.drop_constraint('setting_created_by_user_id_fkey', 'setting', type_='foreignkey')
    op.drop_column('setting', 'created_by_user_id')

    op.add_column('setting', sa.Column('created_by_db_user', sa.Text, nullable=True))
    op.execute("UPDATE setting SET created_by_db_user = 'unknown_user'")

    op.add_column('setting_history', sa.Column('created_by_db_user', sa.Text, nullable=True))
    op.execute("UPDATE setting_history SET created_by_db_user = 'unknown_user'")
    op.alter_column('setting_history', 'created_by_db_user', nullable=False)

    op.add_column('setting_history', sa.Column('deleted_by_db_user', sa.Text, nullable=True))

    op.drop_constraint(
        'setting_history_created_by_user_id_fkey', 'setting_history', type_='foreignkey'
    )
    op.drop_constraint(
        'setting_history_deleted_by_user_id_fkey', 'setting_history', type_='foreignkey'
    )
    op.drop_column('setting_history', 'created_by_user_id')
    op.drop_column('setting_history', 'deleted_by_user_id')

    op.drop_constraint(
        'setting_history_service_name_id_fkey', 'setting_history', type_='foreignkey'
    )
    op.alter_column('setting_history', 'service_name_id', type_=sa.Text())
    replace_service_id_to_service_name(sa.Table('setting_history', meta, autoload=True))
    op.alter_column(
        'setting_history', column_name='service_name_id', new_column_name='service_name'
    )

    op.drop_table('token')
    op.drop_table('user')
    op.drop_table('service_name')

    op.execute("drop type tokentype;")
    op.execute("drop type userrole;")

    op.execute(create_triggers)


create_triggers = """
    CREATE FUNCTION create_history_entry_for_setting() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            INSERT INTO setting_history (
                     name,
                     value,
                     value_type,
                     is_disabled,
                     service_name,
                     created_by_db_user,
                     updated_at
            )
            VALUES (
                    OLD.name,
                    OLD.value,
                    OLD.value_type,
                    OLD.is_disabled,
                    OLD.service_name,
                    OLD.created_by_db_user,
                    OLD.updated_at
            );
        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO setting_history (
                     name,
                     value,
                     value_type,
                     is_disabled,
                     service_name,
                     created_by_db_user,
                     updated_at,
                     is_deleted,
                     deleted_by_db_user
            )
            VALUES (
                    OLD.name,
                    OLD.value,
                    OLD.value_type,
                    OLD.is_disabled,
                    OLD.service_name,
                    OLD.created_by_db_user,
                    OLD.updated_at,
                    true,
                    session_user
            );
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql' SECURITY DEFINER;

    CREATE TRIGGER trigger_create_history_entry_for_setting
        AFTER INSERT OR UPDATE OR DELETE
        ON setting
        FOR EACH ROW
    EXECUTE PROCEDURE create_history_entry_for_setting();

    CREATE FUNCTION fill_user_in_setting_row() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP IN ('INSERT', 'UPDATE') THEN
            NEW.created_by_db_user = session_user;
            NEW.updated_at = current_timestamp;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql' SECURITY DEFINER;

    CREATE TRIGGER trigger_fill_user_in_setting_row
        BEFORE INSERT OR UPDATE
        ON setting
        FOR EACH ROW
    EXECUTE PROCEDURE fill_user_in_setting_row();
"""  # noqa=E501
