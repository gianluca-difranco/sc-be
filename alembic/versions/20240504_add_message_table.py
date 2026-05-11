'''add_message_table

Revision ID: 20240504_add_message_table
Revises: d8b8edfdbfa6  # previous migration (initial setup)
Create Date: 2024-05-04 20:00:00.000000
'''

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240504_add_message_table'
down_revision = 'f37b1e7d16bc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'message',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )


def downgrade():
    op.drop_table('message')
