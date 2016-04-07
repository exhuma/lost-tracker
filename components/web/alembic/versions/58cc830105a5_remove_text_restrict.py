"""Remove text restrictions

Revision ID: 58cc830105a5
Revises: 23097c06462d
Create Date: 2013-05-05 12:01:03.252798

"""

# revision identifiers, used by Alembic.
revision = '58cc830105a5'
down_revision = '23097c06462d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(table_name='group', column_name='name',
                    type_=sa.Unicode)
    op.alter_column(table_name='group', column_name='contact',
                    type_=sa.Unicode)
    op.alter_column(table_name='group', column_name='phone',
                    type_=sa.Unicode)
    op.alter_column(table_name='group', column_name='start_time',
                    type_=sa.Unicode)


def downgrade():
    print(80 * "*")
    print("WARNING: The following columns might get truncated:")
    print("    - group.name")
    print("    - group.contact")
    print("    - group.phone")
    print("    - group.start_time")
    print(80 * "*")
    print("Creating backup table as group_{0}".format(revision))
    op.execute('CREATE TABLE group_{0} AS '
               'SELECT * FROM "group"'.format(revision))
    print("If everything went well, you may delete the backup table!")
    print(80 * "*")
    op.execute('UPDATE "group" SET '
               'name=substring(name from 1 for 50), '
               'contact=substring(contact from 1 for 50), '
               'phone=substring(phone from 1 for 20), '
               'start_time=substring(start_time from 1 for 5)')

    op.alter_column(table_name='group', column_name='name',
                    type_=sa.Unicode(50))
    op.alter_column(table_name='group', column_name='contact',
                    type_=sa.Unicode(50))
    op.alter_column(table_name='group', column_name='phone',
                    type_=sa.Unicode(20))
    op.alter_column(table_name='group', column_name='start_time',
                    type_=sa.Unicode(5))
