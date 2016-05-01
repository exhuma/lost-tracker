"""timed station states

Revision ID: b7058aa347cd
Revises: bd6e5a1fe234
Create Date: 2016-05-01 16:58:53.871600

"""

# revision identifiers, used by Alembic.
revision = 'b7058aa347cd'
down_revision = 'bd6e5a1fe234'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group_station_state',
                  sa.Column('updated',
                            sa.DateTime(timezone=True),
                            nullable=False,
                            server_default=sa.func.now()))


def downgrade():
    op.drop_column('group_station_state', 'updated')
