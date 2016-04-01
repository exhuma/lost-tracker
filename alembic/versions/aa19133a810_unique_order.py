"""unique-order

Revision ID: aa19133a810
Revises: 22d939c3e0fb
Create Date: 2016-03-10 13:53:53.601764

"""

# revision identifiers, used by Alembic.
revision = 'aa19133a810'
down_revision = '22d939c3e0fb'

from alembic import op


def make_unique_values(tablename):
    bind = op.get_bind()
    result = bind.execute('SELECT "order", ARRAY_AGG("id") '
                          'FROM "%s" '
                          'GROUP BY "order"' % tablename)
    for order_value, row_ids in result:
        offset = 1
        for row_id in row_ids[1:]:
            new_value = order_value + offset
            bind.execute('UPDATE "' + tablename + '" SET "order"=%s '
                         'WHERE id=%s', [new_value, row_id])
            print('Replaced order of %s #%d with %d' % (
                tablename, row_id, new_value))
            offset += 1


def upgrade():
    make_unique_values('group')
    make_unique_values('form')
    make_unique_values('group')
    op.create_unique_constraint("unique_station_order", "station", ["order"])
    op.create_unique_constraint("unique_form_order", "form", ["order"])
    op.create_unique_constraint("unique_group_order", "group", ["order"])


def downgrade():
    op.drop_constraint("unique_station_order", "station")
    op.drop_constraint("unique_form_order", "form")
    op.drop_constraint("unique_group_order", "group")
