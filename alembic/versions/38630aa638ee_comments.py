"""comments

Revision ID: 38630aa638ee
Revises: aa19133a810
Create Date: 2016-03-10 20:51:23.260037

"""

# revision identifiers, used by Alembic.
revision = '38630aa638ee'
down_revision = 'aa19133a810'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('content', sa.Unicode),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id')),
        sa.Column('inserted', sa.DateTime, server_default='NOW()'),
        sa.Column('updated', sa.DateTime))


def downgrade():
    op.drop_table('messages')
