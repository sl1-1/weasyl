"""Convert user_streams timestamps to Datetime

Revision ID: 1e2c6b575c20
Revises: bd50eeb393ae
Create Date: 2020-02-27 19:27:04.812000

"""

# revision identifiers, used by Alembic.
revision = '1e2c6b575c20'
down_revision = 'bd50eeb393ae'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_streams', 'start_time',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (start_time-18000) * interval '1 second';")
    op.alter_column('user_streams', 'end_time',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (end_time-18000) * interval '1 second';")


def downgrade():
    pass
