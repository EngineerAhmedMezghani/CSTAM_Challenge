from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobStage(StrEnum):
    DISCOVERY = "DISCOVERY"
    CRAWLING = "CRAWLING"
    CLASSIFICATION = "CLASSIFICATION"
    EXTRACTION = "EXTRACTION"
    DEDUPLICATION = "DEDUPLICATION"
    COMPLETED = "COMPLETED"


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    input_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.PENDING.value, index=True)
    current_stage: Mapped[str] = mapped_column(String(30), nullable=False, default=JobStage.DISCOVERY.value, server_default="DISCOVERY")
    max_depth: Mapped[int] = mapped_column(default=3, server_default="3")
    max_pages: Mapped[int] = mapped_column(default=50, server_default="50")
    pages_visited: Mapped[int] = mapped_column(default=0, server_default="0")
    pages_discovered: Mapped[int] = mapped_column(default=0, server_default="0")
    tender_pages_found: Mapped[int] = mapped_column(default=0, server_default="0")
    tenders_extracted: Mapped[int] = mapped_column(default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenders: Mapped[list["Tender"]] = relationship(
        "Tender", back_populates="job", cascade="all, delete-orphan"
    )


from app.models.tender import Tender  # noqa: E402,F401
