"""refactoring db tables

Revision ID: 274098d8e256
Revises: 576f9300dac3
Create Date: 2022-09-19 22:17:02.232745

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '274098d8e256'
down_revision = '576f9300dac3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'setting_history',
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    op.add_column('setting_history', sa.Column('deleted_by_db_user', sa.Text(), nullable=True))

    op.drop_column('setting_history', 'setting_id')

    op.alter_column('setting', column_name='user_name', new_column_name='created_by_db_user')
    op.alter_column(
        'setting_history', column_name='user_name', new_column_name='created_by_db_user'
    )

    op.execute('DROP TRIGGER trigger_create_history_entry_for_setting ON setting;')
    op.execute('DROP FUNCTION create_history_entry_for_setting;')
    op.execute(upgrade_trigger_create_history_entry_for_setting)

    op.execute('DROP TRIGGER trigger_fill_user_in_setting_row ON setting;')
    op.execute('DROP FUNCTION fill_user_in_setting_row;')
    op.execute(upgrade_trigger_fill_user_in_setting_row)


def downgrade() -> None:
    op.drop_column('setting_history', 'deleted_by_db_user')
    op.drop_column('setting_history', 'is_deleted')

    op.add_column(
        'setting_history', sa.Column('setting_id', sa.INTEGER(), autoincrement=False, nullable=True)
    )

    op.alter_column('setting', column_name='created_by_db_user', new_column_name='user_name')
    op.alter_column(
        'setting_history', column_name='created_by_db_user', new_column_name='user_name'
    )

    op.execute('DROP TRIGGER trigger_create_history_entry_for_setting ON setting;')
    op.execute('DROP FUNCTION create_history_entry_for_setting;')
    op.execute(downgrade_trigger_create_history_entry_for_setting)

    op.execute('DROP TRIGGER trigger_fill_user_in_setting_row ON setting;')
    op.execute('DROP FUNCTION fill_user_in_setting_row;')
    op.execute(downgrade_trigger_fill_user_in_setting_row)


upgrade_trigger_create_history_entry_for_setting = """
    CREATE FUNCTION create_history_entry_for_setting() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            INSERT INTO setting_history (
                     name,
                     value,
                     value_type,
                     disable,
                     service_name,
                     created_by_db_user,
                     updated_at
            )
            VALUES (
                    OLD.name,
                    OLD.value,
                    OLD.value_type,
                    OLD.disable,
                    OLD.service_name,
                    OLD.created_by_db_user,
                    OLD.updated_at
            );
        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO setting_history (
                     name,
                     value,
                     value_type,
                     disable,
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
                    OLD.disable,
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
"""  # noqa=E501

upgrade_trigger_fill_user_in_setting_row = """
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
"""

downgrade_trigger_create_history_entry_for_setting = """
    CREATE FUNCTION create_history_entry_for_setting() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP = 'UPDATE'
        THEN
            INSERT INTO setting_history (setting_id, name, value, value_type, disable, service_name, user_name, updated_at)
            VALUES (OLD.id, OLD.name, OLD.value, OLD.value_type, OLD.disable, OLD.service_name, OLD.user_name, OLD.updated_at);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql' SECURITY DEFINER;

    CREATE TRIGGER trigger_create_history_entry_for_setting
        AFTER INSERT OR UPDATE
        ON setting
        FOR EACH ROW
    EXECUTE PROCEDURE create_history_entry_for_setting();
"""  # noqa=E501

downgrade_trigger_fill_user_in_setting_row = """
    CREATE FUNCTION fill_user_in_setting_row() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE'
        THEN
            NEW.user_name = current_user;
            NEW.updated_at = current_timestamp;
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE 'plpgsql' SECURITY DEFINER;

    CREATE TRIGGER trigger_fill_user_in_setting_row
        BEFORE INSERT OR UPDATE
        ON setting
        FOR EACH ROW
    EXECUTE PROCEDURE fill_user_in_setting_row();
"""
