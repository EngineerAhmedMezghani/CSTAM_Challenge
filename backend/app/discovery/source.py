import logging

from bs4 import BeautifulSoup

from app.discovery.crawler import CrawlConfig, DiscoveryCrawler
from app.discovery.models import PageType
from app.scrapers.base import TenderData
from app.scrapers.generic_extractor import GenericExtractor, clean_text

logger = logging.getLogger(__name__)


class GenericWebSource:
    """Coordinates bounded discovery and reuses the existing HTML extractor."""

    def __init__(self, extractor: GenericExtractor | None = None, config: CrawlConfig | None = None, progress_callback=None):
        self.extractor = extractor or GenericExtractor()
        self.config = config or CrawlConfig(request_timeout=self.extractor.timeout)
        self.progress_callback = progress_callback

    def discover_and_extract(self, root_url: str) -> tuple[list[TenderData], object]:
        crawler = DiscoveryCrawler(
            self.extractor.fetch_html,
            config=self.config,
            progress_callback=self.progress_callback,
        )
        pages, stats = crawler.crawl(root_url)
        extracted: list[TenderData] = []
        for page in pages:
            if page.classification.page_type != PageType.TENDER_DETAIL:
                continue
            items = self.extractor.extract_from_html(page.html, page.url)
            if not items:
                continue
            for tender in items[:1]:
                if not tender.title:
                    soup = BeautifulSoup(page.html, "lxml")
                    heading = soup.find(["h1", "h2", "h3"])
                    tender.title = clean_text(heading.get_text(" ") if heading else None)
                tender.page_type = page.classification.page_type.value
                tender.confidence_score = page.classification.confidence
                tender.confidence_signals = page.classification.signals
                tender.discovery_url = root_url
                tender.discovery_depth = page.depth
                tender.discovery_path = page.discovery_path
                extracted.append(tender)
        logger.info("[EXTRACTOR] Extracted %s tenders from discovered pages", len(extracted))
        return extracted, stats
