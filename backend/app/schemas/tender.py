from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TenderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    source_url: HttpUrl
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    contact: str | None = None
    published_date: date | None = None
    deadline: date | None = None
    documents: list[HttpUrl] = Field(default_factory=list)
    extraction_method: str
    page_type: str
    confidence_score: float | None = None
    confidence_signals: dict[str, bool] = Field(default_factory=dict)
    discovery_url: HttpUrl | None = None
    discovery_depth: int | None = None
    discovery_path: list[HttpUrl] = Field(default_factory=list)
    scraped_at: datetime


class TenderListResponse(BaseModel):
    items: list[TenderResponse]
    total: int
    page: int
    page_size: int
