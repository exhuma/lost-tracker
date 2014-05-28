"""simple-auth

Revision ID: 8faadcbeda5
Revises: 986ba0fc1c7
Create Date: 2014-05-28 19:16:08.290579

"""

# revision identifiers, used by Alembic.
revision = '8faadcbeda5'
down_revision = '986ba0fc1c7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('admin', sa.Boolean,
                                    server_default='false'))

def downgrade():
    op.drop_column('user', 'admin')
