"""participants

Revision ID: bd6e5a1fe234
Revises: ebc7011497c7
Create Date: 2016-04-04 22:05:20.338591

"""

# revision identifiers, used by Alembic.
revision = 'bd6e5a1fe234'
down_revision = 'ebc7011497c7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group',
                  sa.Column('num_participants',
                            sa.Integer(),
                            server_default='0'))


def downgrade():
    op.drop_column('group', 'num_participants')
