"""drop malicious_activity_briefing from scenario appendices

Revision ID: 8f6e1f72ecce
Revises: 4bdaa3f814c7
Create Date: 2026-06-11 14:28:22.280181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f6e1f72ecce'
down_revision: Union[str, Sequence[str], None] = '4bdaa3f814c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


scenarios = sa.table(
    "scenarios",
    sa.column("id", sa.String),
    sa.column("appendices", sa.JSON),
)


def upgrade() -> None:
    """Strip the removed malicious_activity_briefing key from every scenario's appendices."""
    conn = op.get_bind()
    rows = conn.execute(sa.select(scenarios.c.id, scenarios.c.appendices)).fetchall()
    for row_id, appendices in rows:
        if isinstance(appendices, dict) and "malicious_activity_briefing" in appendices:
            cleaned = {k: v for k, v in appendices.items() if k != "malicious_activity_briefing"}
            conn.execute(
                sa.update(scenarios).where(scenarios.c.id == row_id).values(appendices=cleaned)
            )


def downgrade() -> None:
    """No-op: the dropped briefing content is not reconstructable."""
