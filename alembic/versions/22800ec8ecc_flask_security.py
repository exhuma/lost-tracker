"""flask-security

Revision ID: 22800ec8ecc
Revises: 42b5fb49f592
Create Date: 2016-02-21 17:09:25.201945

"""

# revision identifiers, used by Alembic.
revision = '22800ec8ecc'
down_revision = '42b5fb49f592'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Modify User table
    op.drop_constraint('user_pkey', 'user')
    op.drop_column('user', 'login')
    op.drop_column('user', 'admin')
    op.add_column('user', sa.Column('id', sa.Integer(), primary_key=True))
    op.create_unique_constraint("unique_user_id", "user", ["id"])
    op.create_unique_constraint("unique_user", "user", ["email"])
    op.add_column('user', sa.Column('active', sa.Boolean()))
    op.add_column('user', sa.Column('confirmed_at', sa.DateTime()))

    # Create new needed tables
    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.Unicode(80), unique=True),
        sa.Column('description', sa.Unicode(255)))
    op.create_table(
        'roles_users',
        sa.Column('user', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('role', sa.Integer(), sa.ForeignKey('role.id')))


def downgrade():
    op.drop_table('roles_users')
    op.drop_table('role')
    op.drop_constraint('user_pkey', 'user')
    op.drop_constraint('unique_user_id', 'user')
    op.drop_column('user', 'id')
    op.drop_column('user', 'active')
    op.drop_column('user', 'confirmed_at')
    op.add_column('user', sa.Column('login', sa.Unicode(100)))
    op.add_column('user', sa.Column('admin', sa.Boolean(),
                                    server_default='false'))
    op.execute('UPDATE "user" SET login=email')
    op.create_primary_key('user_pkey', 'user', ['login'])
