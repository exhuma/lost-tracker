"""Group Direction Type

Revision ID: 23097c06462d
Revises: c6fc54f7c06
Create Date: 2013-05-03 12:05:58.333948

"""

# revision identifiers, used by Alembic.
revision = '23097c06462d'
down_revision = 'c6fc54f7c06'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

from lost_tracker.models import DIR_A, DIR_B


group = table(
    'group',
    column('direction', sa.Unicode))


def upgrade():
    op.alter_column(
        table_name='group',
        column_name='direction',
        type_=sa.Unicode())
    op.execute(
        group.update().where(
            group.c.direction == 'true').values(
                {'direction': op.inline_literal(DIR_A)}))
    op.execute(
        group.update().where(
            group.c.direction == 'false').values(
                {'direction': op.inline_literal(DIR_B)}))


def downgrade():
    op.execute(
        group.update().where(
            group.c.direction == DIR_A).values(
                {'direction': op.inline_literal(u'true')}))
    op.execute(
        group.update().where(
            group.c.direction == DIR_B).values(
                {'direction': op.inline_literal(u'false')}))
    op.execute('ALTER TABLE "group" '
               'ALTER direction TYPE boolean '
               'USING (direction::boolean)')
