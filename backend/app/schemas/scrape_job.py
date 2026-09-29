from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.models.scrape_job import JobStage, JobStatus


class ScrapeJobCreate(BaseModel):
    url: AnyHttpUrl
    max_depth: int = Field(default=3, ge=0, le=10)
    max_pages: int = Field(default=50, ge=1, le=500)

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported")
        return value


class ScrapeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_url: str
    status: JobStatus
    current_stage: JobStage
    max_depth: int
    max_pages: int
    pages_visited: int
    pages_discovered: int
    tender_pages_found: int
    tenders_extracted: int
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class ScrapeAcceptedResponse(BaseModel):
    job_id: UUID
    status: JobStatus
