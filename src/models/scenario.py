from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    scenario_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    exercise_overview: Mapped[dict] = mapped_column(JSON, default=dict)
    participant_roles: Mapped[dict] = mapped_column(JSON, default=dict)
    exercise_guidelines: Mapped[list] = mapped_column(JSON, default=list)
    scenario_details: Mapped[dict] = mapped_column(JSON, default=dict)
    modules: Mapped[list] = mapped_column(JSON, default=list)
    hotwash: Mapped[dict] = mapped_column(JSON, default=dict)
    appendices: Mapped[dict] = mapped_column(JSON, default=dict)
    success_criteria: Mapped[list] = mapped_column(JSON, default=list)

    title: Mapped[str] = mapped_column(String, index=True, default="")
    scenario_type: Mapped[str] = mapped_column(String, default="")
    framing: Mapped[str] = mapped_column(String, default="")
    difficulty: Mapped[str] = mapped_column(String, default="")
    module_count: Mapped[int] = mapped_column(Integer, default=0)
    inject_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Scenario {self.scenario_id!r} {self.title!r}>"
