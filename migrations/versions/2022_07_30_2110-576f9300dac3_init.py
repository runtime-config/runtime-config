"""init

Revision ID: 576f9300dac3
Revises:
Create Date: 2022-07-30 21:10:52.406512

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '576f9300dac3'
down_revision = None
branch_labels = None
depends_on = None

trigger_fill_user_in_setting_row = """
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

trigger_create_history_entry_for_setting = """
    CREATE FUNCTION create_history_entry_for_setting() RETURNS trigger AS
    $$
    BEGIN
        IF TG_OP = 'UPDATE'
        THEN
            INSERT INTO setting_history (setting_id, name, value, value_type, disable,
                                         service_name, user_name, updated_at)
            VALUES (OLD.id, OLD.name, OLD.value, OLD.value_type, OLD.disable,
                    OLD.service_name, OLD.user_name, OLD.updated_at);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql' SECURITY DEFINER;

    CREATE TRIGGER trigger_create_history_entry_for_setting
        AFTER INSERT OR UPDATE
        ON setting
        FOR EACH ROW
    EXECUTE PROCEDURE create_history_entry_for_setting();
"""


def upgrade() -> None:
    op.create_table(
        'setting',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column(
            'value_type',
            sa.Enum('str', 'int', 'bool', 'null', 'json', name='settingvaluetype'),
            nullable=False,
        ),
        sa.Column('disable', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('service_name', sa.Text(), nullable=False),
        sa.Column('user_name', sa.Text()),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'setting_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column(
            'value_type',
            sa.Enum('str', 'int', 'bool', 'null', 'json', name='settingvaluetype'),
            nullable=False,
        ),
        sa.Column('disable', sa.Boolean(), nullable=False),
        sa.Column('service_name', sa.Text(), nullable=False),
        sa.Column('user_name', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint(
        'unique_setting_name_per_service', 'setting', ['name', 'service_name']
    )
    op.execute(trigger_fill_user_in_setting_row)
    op.execute(trigger_create_history_entry_for_setting)


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER trigger_fill_user_in_setting_row ON setting;
        DROP FUNCTION fill_user_in_setting_row;
        """
    )
    op.execute(
        """
        DROP TRIGGER trigger_create_history_entry_for_setting ON setting;
        DROP FUNCTION create_history_entry_for_setting;
        """
    )
    op.drop_table('setting_history')
    op.drop_constraint('unique_setting_name_per_service', 'setting', type_='unique')
    op.drop_table('setting')
    op.execute('DROP TYPE settingvaluetype')
