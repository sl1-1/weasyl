"""Remove unused column `submission.fave_count`

Revision ID: 999833c1fcf9
Revises: f30dc3b5856a
Create Date: 2017-10-13 17:10:22.671782

"""

# revision identifiers, used by Alembic.
revision = '999833c1fcf9'
down_revision = 'f30dc3b5856a'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submission', 'fave_count')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submission', sa.Column('fave_count', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
