"""default-cancelled-state

Revision ID: 48d6dc1b7728
Revises: 4ffd54bb56a2
Create Date: 2014-03-26 21:10:40.083066

"""

# revision identifiers, used by Alembic.
revision = '48d6dc1b7728'
down_revision = '4ffd54bb56a2'

from alembic import op


def upgrade():
    op.execute('ALTER TABLE "group" ALTER COLUMN cancelled SET DEFAULT false')
    op.execute('UPDATE "group" SET cancelled=false WHERE cancelled IS NULL')


def downgrade():
    pass
