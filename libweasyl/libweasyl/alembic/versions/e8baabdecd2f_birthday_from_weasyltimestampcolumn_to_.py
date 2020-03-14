"""Birthday from WeasylTimestampColumn to date

Revision ID: e8baabdecd2f
Revises: e0320dc462db
Create Date: 2020-03-14 13:18:55.552000

"""

# revision identifiers, used by Alembic.
revision = 'e8baabdecd2f'
down_revision = 'e0320dc462db'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('logincreate', 'birthday',
               existing_type=sa.INTEGER(),
               type_=sa.Date(),
               existing_nullable=False,
               postgresql_using="to_timestamp(birthday + 18000)::date")
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.INTEGER(),
               type_=sa.Date(),
               existing_nullable=False,
               postgresql_using="to_timestamp(birthday + 18000)::date")


def downgrade():
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.Date(),
               type_=sa.INTEGER(),
               existing_nullable=False,
               postgresql_using="extract(epoch from birthday) - 18000")
    op.alter_column('logincreate', 'birthday',
               existing_type=sa.Date(),
               type_=sa.INTEGER(),
               existing_nullable=False,
               postgresql_using="extract(epoch from birthday) - 18000")
