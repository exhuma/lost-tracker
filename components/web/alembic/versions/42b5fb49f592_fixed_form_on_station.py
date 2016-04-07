"""fixed-form-on-station

Revision ID: 42b5fb49f592
Revises: c24c0f68c67
Create Date: 2015-05-01 17:49:29.751617

"""

# revision identifiers, used by Alembic.
revision = '42b5fb49f592'
down_revision = 'c24c0f68c67'

from alembic import op
from sqlalchemy import Column, Integer


def upgrade():
    op.add_column('group_station_state', Column(
        'form_score', Integer, nullable=True, server_default=None))


def downgrade():
    op.drop_column('group_station_state', 'form_score')
