"""add-group-fields

Revision ID: 439f913fbaf6
Revises: 40b6dd1e4f5d
Create Date: 2014-03-24 18:50:04.059176

"""

# revision identifiers, used by Alembic.
revision = '439f913fbaf6'
down_revision = '40b6dd1e4f5d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('comments', sa.Unicode))
    op.add_column('group', sa.Column('is_confirmed', sa.Boolean,
                                     server_default='false',
                                     default=False))
    op.add_column('group', sa.Column('confirmation_key', sa.Unicode(20),
                                     unique=True))


def downgrade():
    op.drop_column('group', 'comments')
    op.drop_column('group', 'is_confirmed')
    op.drop_column('group', 'confirmation_key')
