"""final-station

Revision ID: 35b9d6e63ec3
Revises: b7058aa347cd
Create Date: 2016-05-05 02:12:43.568109

"""

# revision identifiers, used by Alembic.
revision = '35b9d6e63ec3'
down_revision = 'b7058aa347cd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('finish_time',
                                     sa.DateTime,
                                     default=None,
                                     server_default=None))
    op.add_column('station', sa.Column('is_end',
                                       sa.Boolean,
                                       default=False,
                                       server_default='false'))


def downgrade():
    op.drop_column('group', 'finish_time')
    op.drop_column('station', 'is_end')
