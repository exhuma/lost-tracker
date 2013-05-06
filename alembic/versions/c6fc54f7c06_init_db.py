"""Init DB

Revision ID: c6fc54f7c06
Revises: None
Create Date: 2013-05-03 11:21:00.290505

"""

# revision identifiers, used by Alembic.
revision = 'c6fc54f7c06'
down_revision = None

from alembic import op
import sqlalchemy as sa
from lost_tracker.models import STATE_UNKNOWN


def upgrade():
    op.create_table(
        'group',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Unicode(50), unique=True),
        sa.Column('order', sa.Integer),
        sa.Column('cancelled', sa.Boolean),
        sa.Column('contact', sa.Unicode(50)),
        sa.Column('phone', sa.Unicode(20)),
        sa.Column('direction', sa.Boolean),
        sa.Column('start_time', sa.Unicode(5)))

    op.create_table(
        'station',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Unicode(50), unique=True),
        sa.Column('order', sa.Integer),
        sa.Column('contact', sa.Unicode(50)),
        sa.Column('phone', sa.Unicode(20)))

    op.create_table(
        'form',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('name', sa.Unicode(20)),
        sa.Column('max_score', sa.Integer))

    op.create_table(
        'form_scores',
        sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id')),
        sa.Column('form_id', sa.Integer, sa.ForeignKey('form.id')),
        sa.Column('score', sa.Integer, default=0),
        sa.PrimaryKeyConstraint('group_id', 'form_id'))

    op.create_table(
        'group_station_state',
        sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'),
                  primary_key=True),
        sa.Column('station_id', sa.Integer, sa.ForeignKey('station.id'),
                  primary_key=True),
        sa.Column('state', sa.Integer, default=STATE_UNKNOWN),
        sa.Column('score', sa.Integer, nullable=True, default=None))


def downgrade():
    op.drop_table('group_station_state')
    op.drop_table('form_scores')
    op.drop_table('form')
    op.drop_table('station')
    op.drop_table('group')
