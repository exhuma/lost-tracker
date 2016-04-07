"""vegetarians

Revision ID: ebc7011497c7
Revises: 1ef3396d6890
Create Date: 2016-03-30 20:47:28.678475

"""

# revision identifiers, used by Alembic.
revision = 'ebc7011497c7'
down_revision = '1ef3396d6890'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group',
                  sa.Column('num_vegetarians',
                            sa.Integer(),
                            server_default='0'))


def downgrade():
    op.drop_column('group', 'num_vegetarians')
