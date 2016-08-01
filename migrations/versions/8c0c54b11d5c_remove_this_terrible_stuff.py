"""Remove this terrible stuff.

Revision ID: 8c0c54b11d5c
Revises: aa3fe8daf971
Create Date: 2016-08-01 20:32:49.243941

"""

# revision identifiers, used by Alembic.
revision = '8c0c54b11d5c'
down_revision = 'aa3fe8daf971'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###

    conn = op.get_bind()
    conn.execute("DROP TABLE member CASCADE")
    conn.execute('DROP TABLE "user" CASCADE')
    conn.execute('DROP TABLE channel CASCADE')
    conn.execute('DROP TABLE message CASCADE')
    conn.execute('DROP TABLE server CASCADE')
    conn.execute('DROP TABLE nickname_change CASCADE')
    conn.execute('DROP TABLE username_change CASCADE')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('channel', sa.Column('server_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key('channel_server_id_fkey', 'channel', 'server', ['server_id'], ['id'])
    op.create_table('username_change',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('before', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('after', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('changed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='username_change_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='username_change_pkey')
    )
    op.create_table('nickname_change',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('before', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('after', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('member_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('changed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], name='nickname_change_member_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='nickname_change_pkey')
    )
    op.create_table('server',
    sa.Column('id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['member.id'], name='server_owner_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='server_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('message',
    sa.Column('id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('content', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('deleted', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('channel_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('member_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['channel_id'], ['channel.id'], name='message_channel_id_fkey'),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], name='message_member_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='message_pkey')
    )
    op.create_table('user',
    sa.Column('id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='user_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('member',
    sa.Column('id', sa.BIGINT(), nullable=False),
    sa.Column('joined_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('server_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], name='member_server_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='member_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='member_pkey')
    )
    ### end Alembic commands ###
