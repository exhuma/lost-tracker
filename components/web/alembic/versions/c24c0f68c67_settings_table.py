"""settings_table

Revision ID: c24c0f68c67
Revises: 4131dd623af6
Create Date: 2015-04-26 13:50:36.196944

"""

# revision identifiers, used by Alembic.
revision = 'c24c0f68c67'
down_revision = '4131dd623af6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'settings',
        sa.Column('key', sa.Unicode(20), primary_key=True),
        sa.Column('value', sa.Unicode()),
        sa.Column('description', sa.Unicode())
    )


def downgrade():
    op.drop_table('settings')
