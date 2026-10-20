"""drop audit fields, rename uploaded_at to created_at

Revision ID: 8b43d5aabfa9
Revises: 10239baf7a59
Create Date: 2026-05-28 11:54:57.988024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b43d5aabfa9'
down_revision: Union[str, Sequence[str], None] = '10239baf7a59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('scenarios', schema=None) as batch_op:
        batch_op.alter_column('uploaded_at', new_column_name='created_at')
        batch_op.drop_column('uploaded_by')
        batch_op.drop_column('original_filename')


def downgrade() -> None:
    """Downgrade schema."""
    # Lossy: uploaded_by becomes '' for all rows; original_filename becomes NULL.
    with op.batch_alter_table('scenarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_filename', sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column('uploaded_by', sa.String(), nullable=False, server_default='')
        )
        batch_op.alter_column('created_at', new_column_name='uploaded_at')
