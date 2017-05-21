"""group-message-integrity

Revision ID: 429cf763a9a9
Revises: 29469d1c3b38
Create Date: 2017-05-21 18:41:30.839043

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '429cf763a9a9'
down_revision = '29469d1c3b38'


def upgrade():

    op.execute('ALTER TABLE messages '
               'DROP CONSTRAINT messages_group_id_fkey;')
    op.execute('ALTER TABLE messages '
               'DROP CONSTRAINT messages_user_id_fkey;')
    op.execute('ALTER TABLE messages '
               'ADD CONSTRAINT messages_group_id_fkey '
               'FOREIGN KEY (group_id) REFERENCES "group" (id) '
               'ON DELETE CASCADE ON UPDATE CASCADE')
    op.execute('ALTER TABLE messages '
               'ADD CONSTRAINT messages_user_id_fkey '
               'FOREIGN KEY (user_id) REFERENCES "user" (id) '
               'ON DELETE CASCADE ON UPDATE CASCADE')


def downgrade():
    op.execute('ALTER TABLE messages '
               'DROP CONSTRAINT messages_group_id_fkey;')
    op.execute('ALTER TABLE messages '
               'DROP CONSTRAINT messages_user_id_fkey;')
    op.execute('ALTER TABLE messages '
               'ADD CONSTRAINT messages_group_id_fkey '
               'FOREIGN KEY (group_id) REFERENCES "group" (id)')
    op.execute('ALTER TABLE messages '
               'ADD CONSTRAINT messages_user_id_fkey '
               'FOREIGN KEY (user_id) REFERENCES "user" (id)')
