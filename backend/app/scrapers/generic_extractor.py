import logging
import re
from datetime import date, datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import settings
from app.scrapers.base import BaseScraper, TenderData

logger = logging.getLogger(__name__)

_DATE_PATTERNS = (
    (re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"), "%Y-%m-%d"),
    (re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b"), "%d-%m-%Y"),
)
_KEYWORDS = re.compile(r"appel\s+d['’\s]?offres|tender|rfp|consultation|march[ée]s?\s+publics?|deadline|avis", re.I)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for pattern, date_format in _DATE_PATTERNS:
        match = pattern.search(value)
        if match:
            raw = "-".join(match.groups())
            try:
                return datetime.strptime(raw, date_format).date()
            except ValueError:
                logger.debug("Invalid date ignored", extra={"value": value})
    return None


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


class GenericExtractor(BaseScraper):
    extraction_method = "generic"

    def __init__(self, timeout: float | None = None, max_response_size: int | None = None) -> None:
        self.timeout = timeout or settings.http_timeout
        self.max_response_size = max_response_size or settings.max_response_size

    def fetch_html(self, url: str) -> str:
        logger.info("HTTP request", extra={"url": url})
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "OliveSoftTenderScraper/1.0"})
            response.raise_for_status()
            if len(response.content) > self.max_response_size:
                raise ValueError("Response exceeds the configured maximum size")
            return response.text

    def scrape(self, url: str) -> list[TenderData]:
        html = self.fetch_html(url)
        if not html.strip():
            return []
        return self.extract_from_html(html, url)

    def extract_from_html(self, html: str, source_url: str) -> list[TenderData]:
        soup = BeautifulSoup(html, "lxml")
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        candidates = self._candidate_blocks(soup)
        tenders = [self._extract_block(block, source_url) for block in candidates]
        tenders = [tender for tender in tenders if tender.title or tender.description or tender.documents]
        if tenders:
            return tenders

        page_text = clean_text(soup.get_text(" "))
        if page_text and _KEYWORDS.search(page_text):
            links = self._document_links(soup, source_url)
            return [
                TenderData(
                    source_url=source_url,
                    title=clean_text(soup.title.get_text(" ") if soup.title else None),
                    description=page_text[:4000],
                    documents=links,
                    raw_html_snippet=str(soup)[:5000],
                )
            ]
        return []

    def _candidate_blocks(self, soup: BeautifulSoup) -> list[Tag]:
        selectors = ["article", "tr", ".tender", ".rfp", ".notice", ".appel-offres", ".card"]
        blocks: list[Tag] = []
        seen: set[int] = set()
        for selector in selectors:
            for block in soup.select(selector):
                text = clean_text(block.get_text(" ")) or ""
                if len(text) < 20 or not (_KEYWORDS.search(text) or block.find("a", href=re.compile(r"\.(pdf|docx?|PDF|DOCX?)($|[?#])"))):
                    continue
                marker = id(block)
                if marker not in seen:
                    blocks.append(block)
                    seen.add(marker)
        return blocks

    def _extract_block(self, block: Tag, source_url: str) -> TenderData:
        text = clean_text(block.get_text(" ")) or ""
        heading = block.find(["h1", "h2", "h3", "h4", "h5", "strong", "b"])
        title = clean_text(heading.get_text(" ") if heading else None)
        if not title:
            title = clean_text(block.find("a").get_text(" ") if block.find("a") else None)
        documents = self._document_links(block, source_url)
        dates = [parse_date(text)]
        dates.extend(parse_date(attribute) for element in block.find_all(True) for attribute in [element.get("datetime"), element.get("data-date")])
        valid_dates = [value for value in dates if value]
        deadline = valid_dates[-1] if valid_dates else None
        published = valid_dates[0] if len(valid_dates) > 1 else None
        owner = self._labeled_value(text, r"(?:organisme|organisation|owner|ma[îi]tre d['’]ouvrage)\s*[:\-]\s*([^|;]+)")
        contact = self._labeled_value(text, r"(?:contact|email|e-mail)\s*[:\-]\s*([^|;]+)")
        description = text if text != title else None
        return TenderData(
            source_url=source_url,
            title=title,
            description=description[:4000] if description else None,
            owner=owner,
            contact=contact,
            published_date=published,
            deadline=deadline,
            documents=documents,
            raw_html_snippet=str(block)[:5000],
        )

    @staticmethod
    def _labeled_value(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, re.I)
        return clean_text(match.group(1)) if match else None

    @staticmethod
    def _document_links(element: Tag, source_url: str) -> list[str]:
        links: list[str] = []
        for anchor in element.find_all("a", href=True):
            href = urljoin(source_url, anchor["href"])
            if re.search(r"\.(pdf|doc|docx)(?:$|[?#])", href, re.I) and href not in links:
                links.append(href)
        return links
