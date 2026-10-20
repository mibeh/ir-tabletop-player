from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ScenarioType(str, Enum):
    SUPPLY_CHAIN = "supply_chain"
    PRODUCT_VULNERABILITY = "product_vulnerability"
    CUSTOMER_BREACH = "customer_breach"
    INSIDER_THREAT = "insider_threat"
    RANSOMWARE = "ransomware"
    REGULATORY_NOTIFICATION = "regulatory_notification"
    REPUTATIONAL = "reputational"
    NATION_STATE_PERSISTENT = "nation_state_persistent"


class ExerciseStatus(str, Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    DEBRIEF = "debrief"
    COMPLETE = "complete"


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=ExerciseStatus.AVAILABLE)

    # Catalog link + copied CTEP content
    scenario_catalog_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("scenarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    exercise_overview: Mapped[dict] = mapped_column(JSON, default=dict)
    exercise_guidelines: Mapped[list] = mapped_column(JSON, default=list)
    modules: Mapped[list] = mapped_column(JSON, default=list)
    success_criteria: Mapped[list] = mapped_column(JSON, default=list)
    hotwash: Mapped[dict] = mapped_column(JSON, default=dict)
    appendices: Mapped[dict] = mapped_column(JSON, default=dict)

    # Roster
    participants: Mapped[list] = mapped_column(JSON, default=list)

    # Presentation state
    current_slide: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    furthest_slide: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    debrief_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_total_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Debrief output
    debrief_summary: Mapped[str] = mapped_column(Text, default="")
    follow_up_actions: Mapped[list] = mapped_column(JSON, default=list)

    # Archive
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Exercise {self.title!r} [{self.status}]>"
