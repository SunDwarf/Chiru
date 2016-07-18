"""Change ID to BigInteger

Revision ID: 8cfe5befdaec
Revises: f0d5084d5125
Create Date: 2016-07-18 13:59:09.946780

"""

# revision identifiers, used by Alembic.
revision = '8cfe5befdaec'
down_revision = 'f0d5084d5125'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    conn.execute("ALTER TABLE channel ALTER COLUMN id TYPE BIGINT")
    conn.execute("ALTER TABLE channel_link ALTER COLUMN channel_id TYPE BIGINT")


def downgrade():
    conn = op.get_bind()
    conn.execute("ALTER TABLE channel ALTER COLUMN id TYPE INT")
    conn.execute("ALTER TABLE channel_link ALTER COLUMN channel_id TYPE INT")
