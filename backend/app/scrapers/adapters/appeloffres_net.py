import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import settings
from app.discovery.models import PageType
from app.scrapers.base import BaseScraper, TenderData
from app.scrapers.generic_extractor import GenericExtractor, clean_text, parse_date

logger = logging.getLogger(__name__)


class AppelOffresNetScraper(BaseScraper):
    """Two-pass scraper for the public appeloffres.net listing.

    Detail pages currently require an authenticated subscription. When a detail
    page is unavailable, its public listing row is retained and explicitly
    labelled as a partial listing item instead of a detail page.
    """

    extraction_method = "appeloffres_net"
    _DETAIL_PATH = re.compile(r"^/appels-offres/\d+/?$", re.I)
    _MAX_DETAIL_PAGES = 50

    @staticmethod
    def supports(url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower().removeprefix("www.")
        return hostname == "appeloffres.net"

    def __init__(self) -> None:
        self.generic = GenericExtractor()

    def scrape(self, url: str) -> list[TenderData]:
        listing_html, _ = self._fetch(url)
        listing_items = self._extract_listing_items(listing_html, url)
        if not listing_items:
            logger.warning("No appeloffres.net listing items found", extra={"url": url})
            return []

        results: list[TenderData] = []
        for summary in listing_items[: self._MAX_DETAIL_PAGES]:
            detail = self._extract_detail(summary.source_url)
            results.append(detail or summary)
        return results

    def _fetch(self, url: str) -> tuple[str, str]:
        headers = {"User-Agent": "OliveSoftTenderScraper/1.0"}
        if settings.appeloffres_cookie:
            headers["Cookie"] = settings.appeloffres_cookie
        with httpx.Client(timeout=settings.http_timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            if len(response.content) > settings.max_response_size:
                raise ValueError("Response exceeds the configured maximum size")
            return response.text, str(response.url)

    def _extract_detail(self, url: str) -> TenderData | None:
        try:
            html, final_url = self._fetch(url)
        except httpx.HTTPError:
            logger.exception("Failed to fetch appeloffres.net detail", extra={"url": url})
            return None
        if self._is_login_page(final_url, html):
            logger.info("Detail requires authentication; keeping public summary", extra={"url": url})
            return None

        items = self.generic.extract_from_html(html, url)
        if not items:
            return None
        tender = items[0]
        tender.source_url = url
        tender.extraction_method = self.extraction_method
        tender.page_type = PageType.TENDER_DETAIL.value
        tender.confidence_score = 0.9
        tender.confidence_signals = {
            "detail_path": True,
            "authenticated_detail": bool(settings.appeloffres_cookie),
        }
        return tender

    def _extract_listing_items(self, html: str, listing_url: str) -> list[TenderData]:
        soup = BeautifulSoup(html, "lxml")
        results: list[TenderData] = []
        seen: set[str] = set()
        for row in soup.select("table tbody tr"):
            detail_url = self._detail_url(row, listing_url)
            if not detail_url or detail_url in seen:
                continue
            seen.add(detail_url)
            cells = row.select("td")
            values = [clean_text(cell.get_text(" ")) for cell in cells]
            title = self._cell_title(cells, 1) or (values[1] if len(values) > 1 else None)
            owner = self._cell_title(cells, 3) or (values[3] if len(values) > 3 else None)
            published = parse_date(values[5] if len(values) > 5 else None)
            deadline = parse_date(values[6] if len(values) > 6 else None)
            description = clean_text(" | ".join(value for value in values if value))
            results.append(
                TenderData(
                    source_url=detail_url,
                    title=title,
                    description=description,
                    owner=owner,
                    published_date=published,
                    deadline=deadline,
                    raw_html_snippet=str(row)[:5000],
                    extraction_method="appeloffres_net_listing",
                    page_type=PageType.TENDER_LIST_ITEM.value,
                    confidence_score=0.35,
                    confidence_signals={
                        "detail_path": True,
                        "listing_summary_only": True,
                        "title_truncated": bool(title and "..." in title),
                    },
                    discovery_url=listing_url,
                    discovery_depth=0,
                    discovery_path=[listing_url, detail_url],
                )
            )
        return results

    @classmethod
    def _detail_url(cls, row: Tag, listing_url: str) -> str | None:
        for anchor in row.find_all("a", href=True):
            absolute = urljoin(listing_url, str(anchor["href"]))
            if cls._DETAIL_PATH.match(urlparse(absolute).path):
                return absolute
        return None

    @staticmethod
    def _cell_title(cells: list[Tag], index: int) -> str | None:
        if index >= len(cells):
            return None
        anchor = cells[index].find("a")
        return clean_text(anchor.get("title")) if anchor else None

    @staticmethod
    def _is_login_page(final_url: str, html: str) -> bool:
        if urlparse(final_url).path.rstrip("/") == "/connexion":
            return True
        soup = BeautifulSoup(html, "lxml")
        title = clean_text(soup.title.get_text(" ") if soup.title else None) or ""
        return "connexion à votre espace" in title.casefold()
