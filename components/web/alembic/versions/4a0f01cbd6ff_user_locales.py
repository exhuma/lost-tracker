"""user-locales

Revision ID: 4a0f01cbd6ff
Revises: 1cdab65e5cea
Create Date: 2014-03-30 15:47:40.121359

"""

# revision identifiers, used by Alembic.
revision = '4a0f01cbd6ff'
down_revision = '1cdab65e5cea'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('locale', sa.Unicode(2)))


def downgrade():
    op.drop_column('user', 'locale')
