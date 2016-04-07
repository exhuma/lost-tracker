"""group registration finalized flag

Revision ID: 546a44c5987f
Revises: 48d6dc1b7728
Create Date: 2014-03-27 15:22:17.707668

"""

# revision identifiers, used by Alembic.
revision = '546a44c5987f'
down_revision = '48d6dc1b7728'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column(
                                    'finalized',
                                    sa.Boolean,
                                    server_default='false',
                                    default=False))


def downgrade():
    op.drop_Column('group', 'finalized')
