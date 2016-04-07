"""departure_time

Revision ID: 1ef3396d6890
Revises: 38630aa638ee
Create Date: 2016-03-18 08:44:07.503739

"""

# revision identifiers, used by Alembic.
revision = '1ef3396d6890'
down_revision = '38630aa638ee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('departure_time',
                                     sa.DateTime,
                                     default=None,
                                     server_default=None))
    op.add_column('station', sa.Column('is_start',
                                       sa.Boolean,
                                       default=False,
                                       server_default='false'))


def downgrade():
    op.drop_column('group', 'departure_time')
    op.drop_column('station', 'is_start')
