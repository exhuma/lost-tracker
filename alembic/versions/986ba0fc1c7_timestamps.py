"""timestamps

Revision ID: 986ba0fc1c7
Revises: 4a0f01cbd6ff
Create Date: 2014-05-03 10:18:57.154358

"""

from textwrap import dedent

# revision identifiers, used by Alembic.
revision = '986ba0fc1c7'
down_revision = '4a0f01cbd6ff'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute(dedent('''\
        CREATE OR REPLACE FUNCTION set_updated_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';'''))
    op.execute(dedent('''\
        CREATE TRIGGER group_updated_timestamp
            BEFORE UPDATE ON "group"
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE PROCEDURE set_updated_column();'''))
    op.add_column('group',
                  sa.Column('inserted',
                            sa.DateTime(),
                            server_default=sa.func.now(),
                            default=sa.func.now()))
    op.add_column('group',
                  sa.Column('updated',
                            sa.DateTime()))


def downgrade():
    op.drop_column('group', 'inserted')
    op.drop_column('group', 'updated')
    op.execute('DROP TRIGGER group_updated_timestamp ON "group"')
    op.execute('DROP FUNCTION set_updated_column()')
