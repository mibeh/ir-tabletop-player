"""drop case_studies and secure_by_design_tactics from appendices

Revision ID: 330725cc66a2
Revises: 8f6e1f72ecce
Create Date: 2026-06-12 11:43:31.365180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '330725cc66a2'
down_revision: Union[str, Sequence[str], None] = '8f6e1f72ecce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DROPPED_KEYS = ("case_studies", "secure_by_design_tactics")

scenarios = sa.table(
    "scenarios",
    sa.column("id", sa.String),
    sa.column("appendices", sa.JSON),
)

exercises = sa.table(
    "exercises",
    sa.column("id", sa.String),
    sa.column("appendices", sa.JSON),
)


def _strip(conn, table) -> None:
    rows = conn.execute(sa.select(table.c.id, table.c.appendices)).fetchall()
    for row_id, appendices in rows:
        if not isinstance(appendices, dict):
            continue
        if any(k in appendices for k in _DROPPED_KEYS):
            cleaned = {k: v for k, v in appendices.items() if k not in _DROPPED_KEYS}
            conn.execute(
                sa.update(table).where(table.c.id == row_id).values(appendices=cleaned)
            )


def upgrade() -> None:
    """Strip the removed case_studies / secure_by_design_tactics keys.

    Appendices are deep-copied into exercises at creation, so both the catalog
    rows and any existing exercise rows are cleaned.
    """
    conn = op.get_bind()
    _strip(conn, scenarios)
    _strip(conn, exercises)


def downgrade() -> None:
    """No-op: the dropped appendix content is not reconstructable."""
