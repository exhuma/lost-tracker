"""flask-social

Revision ID: 264d64fe2f20
Revises: 22800ec8ecc
Create Date: 2016-03-01 08:06:55.584672

"""

# revision identifiers, used by Alembic.
revision = '264d64fe2f20'
down_revision = '22800ec8ecc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'connection',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('provider_id', sa.Unicode(255)),
        sa.Column('provider_user_id', sa.Unicode(255)),
        sa.Column('access_token', sa.Unicode(255)),
        sa.Column('secret', sa.Unicode(255)),
        sa.Column('display_name', sa.Unicode(255)),
        sa.Column('profile_url', sa.Unicode(512)),
        sa.Column('image_url', sa.Unicode(512)),
        sa.Column('rank', sa.Integer))


def downgrade():
    op.drop_table('connection')
