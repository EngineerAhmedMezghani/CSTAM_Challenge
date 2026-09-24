from dataclasses import dataclass, field
from enum import StrEnum


class PageType(StrEnum):
    TENDER_LIST = "TENDER_LIST"
    TENDER_DETAIL = "TENDER_DETAIL"
    NEWS = "NEWS"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    EVENT = "EVENT"
    REGULATION = "REGULATION"
    CONTACT = "CONTACT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class LinkCandidate:
    url: str
    anchor_text: str = ""
    title: str = ""
    aria_label: str = ""
    context: str = ""
    score: float = 0.0


@dataclass(slots=True)
class PageClassification:
    page_type: PageType
    confidence: float
    signals: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class DiscoveredPage:
    url: str
    html: str
    depth: int
    discovery_path: list[str]
    classification: PageClassification
    links: list[LinkCandidate] = field(default_factory=list)


@dataclass(slots=True)
class CrawlStats:
    pages_visited: int = 0
    pages_discovered: int = 0
    tender_pages_found: int = 0
    tender_list_pages: int = 0
    tender_detail_pages: int = 0
    news_pages_found: int = 0
    other_pages_found: int = 0
    errors: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "pages_visited": self.pages_visited,
            "pages_discovered": self.pages_discovered,
            "tender_pages_found": self.tender_pages_found,
            "tender_list_pages": self.tender_list_pages,
            "tender_detail_pages": self.tender_detail_pages,
            "news_pages_found": self.news_pages_found,
            "other_pages_found": self.other_pages_found,
            "errors": self.errors,
        }
