"""form-id-sequence

Revision ID: 1cdab65e5cea
Revises: 546a44c5987f
Create Date: 2014-03-30 15:21:20.396045

"""

# revision identifiers, used by Alembic.
revision = '1cdab65e5cea'
down_revision = '546a44c5987f'

from alembic import op


def upgrade():
    op.execute("CREATE SEQUENCE form_id_seq")
    op.execute("ALTER TABLE form ALTER COLUMN id "
               "SET DEFAULT nextval('form_id_seq'::regclass)")


def downgrade():
    op.execute("ALTER TABLE form ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE form_id_seq")
