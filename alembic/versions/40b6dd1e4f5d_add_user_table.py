"""add-user-table

Revision ID: 40b6dd1e4f5d
Revises: 58cc830105a5
Create Date: 2014-03-24 18:44:58.994340

"""

# revision identifiers, used by Alembic.
revision = '40b6dd1e4f5d'
down_revision = '58cc830105a5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'user',
        sa.Column('login', sa.Unicode(100), primary_key=True),
        sa.Column('name', sa.Unicode(100)),
        sa.Column('password', sa.Unicode(100)),
        sa.Column('email', sa.Unicode(100)))


def downgrade():
    op.drop_table('user')
