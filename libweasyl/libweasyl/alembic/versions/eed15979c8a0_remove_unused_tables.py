"""Remove unused tables

Revision ID: eed15979c8a0
Revises: abeefecabdad
Create Date: 2017-05-06 14:22:19.133223

"""

# revision identifiers, used by Alembic.
revision = 'eed15979c8a0'
down_revision = 'abeefecabdad'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('loginaddress')
    op.drop_table('ignorecontent')
    op.drop_table('commission')
    op.drop_table('composition')
    op.drop_table('logininvite')
    op.drop_table('contentview')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contentview',
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('targetid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('type', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('userid', 'targetid', 'type', name='contentview_pkey')
    )
    op.create_table('logininvite',
    sa.Column('email', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unixtime', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('settings', sa.VARCHAR(length=20), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('email', name='logininvite_pkey')
    )
    op.create_table('composition',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('workid', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('unixtime', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='composition_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'workid', name='composition_pkey')
    )
    op.create_table('commission',
    sa.Column('commishid', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('content', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('min_amount', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('max_amount', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('settings', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False),
    sa.Column('unixtime', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='commission_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commishid', name='commission_pkey')
    )
    op.create_table('ignorecontent',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('otherid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='ignorecontent_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='ignorecontent_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid', name='ignorecontent_pkey')
    )
    op.create_table('loginaddress',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('address', sa.VARCHAR(length=40), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='loginaddress_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'address', name='loginaddress_pkey')
    )
    # ### end Alembic commands ###
