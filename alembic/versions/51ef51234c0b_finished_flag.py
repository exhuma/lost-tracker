"""finished-flag

Revision ID: 51ef51234c0b
Revises: 8faadcbeda5
Create Date: 2014-05-28 23:47:42.429447

"""

# revision identifiers, used by Alembic.
revision = '51ef51234c0b'
down_revision = '8faadcbeda5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('completed', sa.Boolean,
                                     server_default='false'))


def downgrade():
    op.drop_column('group', 'completed')
