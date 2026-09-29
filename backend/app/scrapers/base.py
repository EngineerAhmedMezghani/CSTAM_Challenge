from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class TenderData:
    source_url: str
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    contact: str | None = None
    published_date: date | None = None
    deadline: date | None = None
    documents: list[str] = field(default_factory=list)
    raw_html_snippet: str | None = None
    extraction_method: str = "generic"
    page_type: str = "TENDER_DETAIL"
    confidence_score: float | None = None
    confidence_signals: dict[str, bool] = field(default_factory=dict)
    discovery_url: str | None = None
    discovery_depth: int | None = None
    discovery_path: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    extraction_method = "generic"

    @abstractmethod
    def scrape(self, url: str) -> list[TenderData]:
        raise NotImplementedError
