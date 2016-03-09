"""disambiguations

Revision ID: 22d939c3e0fb
Revises: 15184887f8e2
Create Date: 2016-03-09 17:19:42.292217

"""

# revision identifiers, used by Alembic.
revision = '22d939c3e0fb'
down_revision = '15184887f8e2'

from alembic import op


def upgrade():
    op.alter_column('group', 'finalized', new_column_name='accepted')


def downgrade():
    op.alter_column('group', 'accepted', new_column_name='finalized')
