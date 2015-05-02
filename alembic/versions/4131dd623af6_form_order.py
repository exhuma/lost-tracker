"""form-order

Revision ID: 4131dd623af6
Revises: 51ef51234c0b
Create Date: 2015-04-26 08:47:49.428226

"""

# revision identifiers, used by Alembic.
revision = '4131dd623af6'
down_revision = '51ef51234c0b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('form', sa.Column('order', sa.Integer, nullable=False,
                                    server_default='0'))


def downgrade():
    op.drop_column('form', 'order')
