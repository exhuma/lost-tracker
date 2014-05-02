"""add-group-email

Revision ID: 4ffd54bb56a2
Revises: 439f913fbaf6
Create Date: 2014-03-25 18:33:39.942135

"""

# revision identifiers, used by Alembic.
revision = '4ffd54bb56a2'
down_revision = '439f913fbaf6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('email', sa.Unicode))


def downgrade():
    op.drop_column('group', 'email')
