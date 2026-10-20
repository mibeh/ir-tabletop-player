"""add inject_count to scenarios

Revision ID: 4bdaa3f814c7
Revises: 43c96ab0653b
Create Date: 2026-05-29 12:18:35.358164

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4bdaa3f814c7'
down_revision: Union[str, Sequence[str], None] = '43c96ab0653b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('scenarios', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('inject_count', sa.Integer(), nullable=False, server_default='0')
        )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, modules FROM scenarios")).fetchall()
    for row in rows:
        modules = row.modules
        if isinstance(modules, str):
            try:
                modules = json.loads(modules)
            except (TypeError, ValueError):
                modules = []
        modules = modules or []
        total = sum(
            len(m.get('injects', []) or [])
            for m in modules
            if isinstance(m, dict)
        )
        conn.execute(
            sa.text("UPDATE scenarios SET inject_count = :n WHERE id = :id"),
            {"n": total, "id": row.id},
        )


def downgrade() -> None:
    with op.batch_alter_table('scenarios', schema=None) as batch_op:
        batch_op.drop_column('inject_count')
