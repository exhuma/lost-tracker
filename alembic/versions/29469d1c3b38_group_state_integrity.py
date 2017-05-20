"""group-state-integrity

Revision ID: 29469d1c3b38
Revises: 35b9d6e63ec3
Create Date: 2017-05-20 16:40:40.478680

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '29469d1c3b38'
down_revision = '35b9d6e63ec3'


def upgrade():
    op.execute('ALTER TABLE group_station_state '
               'DROP CONSTRAINT group_station_state_group_id_fkey;')
    op.execute('ALTER TABLE group_station_state '
               'DROP CONSTRAINT group_station_state_station_id_fkey;')
    op.execute('ALTER TABLE group_station_state '
               'ADD CONSTRAINT group_station_state_group_id_fk '
               'FOREIGN KEY (group_id) REFERENCES "group" (id) '
               'ON DELETE CASCADE ON UPDATE CASCADE')
    op.execute('ALTER TABLE group_station_state '
               'ADD CONSTRAINT group_station_state_station_id_fk '
               'FOREIGN KEY (station_id) REFERENCES "station" (id) '
               'ON DELETE CASCADE ON UPDATE CASCADE')


def downgrade():
    op.execute('ALTER TABLE group_station_state '
               'DROP CONSTRAINT group_station_state_group_id_fk;')
    op.execute('ALTER TABLE group_station_state '
               'DROP CONSTRAINT group_station_state_station_id_fk;')
    op.execute('ALTER TABLE group_station_state '
               'ADD CONSTRAINT group_station_state_group_id_fkey '
               'FOREIGN KEY (group_id) REFERENCES "group" (id)')
    op.execute('ALTER TABLE group_station_state '
               'ADD CONSTRAINT group_station_state_station_id_fkey '
               'FOREIGN KEY (station_id) REFERENCES "station" (id)')
