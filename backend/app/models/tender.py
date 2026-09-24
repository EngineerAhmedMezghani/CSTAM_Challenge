from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tender(Base):
    __tablename__ = "tenders"
    __table_args__ = (
        Index("ix_tenders_content_hash", "content_hash"),
        Index("ix_tenders_source_url", "source_url"),
        Index("ix_tenders_job_id", "job_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    documents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    raw_html_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str] = mapped_column(Text, nullable=False, default="generic", server_default="generic")
    page_type: Mapped[str] = mapped_column(Text, nullable=False, default="TENDER_DETAIL", server_default="TENDER_DETAIL")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_signals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    discovery_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovery_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovery_path: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped["ScrapeJob"] = relationship("ScrapeJob", back_populates="tenders")
