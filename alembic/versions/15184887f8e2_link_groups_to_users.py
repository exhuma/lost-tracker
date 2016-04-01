"""link-groups-to-users

Revision ID: 15184887f8e2
Revises: 264d64fe2f20
Create Date: 2016-03-08 16:15:02.313910

"""

# revision identifiers, used by Alembic.
revision = '15184887f8e2'
down_revision = '264d64fe2f20'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('group', sa.Column('user_id', sa.Integer, sa.ForeignKey(
        'user.id', on_update='CASCADE', on_delete='SET NULL')))


def downgrade():
    op.drop_column('group', 'user_id')
