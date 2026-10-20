"""remove approval add pause

Revision ID: 10239baf7a59
Revises: dab150eb3075
Create Date: 2026-05-28 10:45:00.519191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10239baf7a59'
down_revision: Union[str, Sequence[str], None] = 'dab150eb3075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column(
            'paused_total_seconds',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ))

    # Data migration: collapse draft/approved -> available, rename active -> in_progress
    op.execute("UPDATE exercises SET status='available' WHERE status IN ('draft', 'approved')")
    op.execute("UPDATE exercises SET status='in_progress' WHERE status='active'")


def downgrade() -> None:
    """Downgrade schema."""
    # Lossy: paused rows collapse to active; pause timing data is dropped
    op.execute("UPDATE exercises SET status='active' WHERE status IN ('in_progress', 'paused')")
    op.execute("UPDATE exercises SET status='draft' WHERE status='available'")

    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.drop_column('paused_total_seconds')
        batch_op.drop_column('paused_at')
