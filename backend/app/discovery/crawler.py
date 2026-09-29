import heapq
import logging
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from app.discovery.link_extractor import extract_links, normalize_url
from app.discovery.models import CrawlStats, DiscoveredPage, PageType
from app.discovery.page_classifier import classify_page
from app.discovery.url_scorer import score_url

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CrawlConfig:
    max_depth: int = 3
    max_pages: int = 50
    request_timeout: float = 20.0
    max_concurrency: int = 1
    same_domain_only: bool = True
    use_playwright_fallback: bool = True


class DiscoveryCrawler:
    def __init__(
        self,
        fetch_html: Callable[[str], str],
        config: CrawlConfig | None = None,
        render_html: Callable[[str], str] | None = None,
        progress_callback: Callable[[CrawlStats], None] | None = None,
    ) -> None:
        self.fetch_html = fetch_html
        self.config = config or CrawlConfig()
        self.render_html = render_html
        self.progress_callback = progress_callback

    def crawl(self, start_url: str) -> tuple[list[DiscoveredPage], CrawlStats]:
        root_url = normalize_url(start_url)
        if not root_url:
            raise ValueError("A valid HTTP or HTTPS URL is required")
        root_host = self._host(root_url)
        queue: list[tuple[float, int, int, str, list[str]]] = [(0.0, 0, 0, root_url, [root_url])]
        queued = {root_url}
        visited: set[str] = set()
        pages: list[DiscoveredPage] = []
        stats = CrawlStats()
        sequence = 0
        logger.info("[DISCOVERY] Starting from %s", root_url)

        while queue and len(visited) < self.config.max_pages:
            _, depth, _, url, path = heapq.heappop(queue)
            if url in visited or depth > self.config.max_depth:
                continue
            visited.add(url)
            stats.pages_visited = len(visited)
            try:
                html = self.fetch_html(url)
                links = extract_links(BeautifulSoup(html, "lxml"), url)
                if self._needs_rendering(html, links) and self.config.use_playwright_fallback and self.render_html:
                    rendered = self.render_html(url)
                    if rendered:
                        html = rendered
                        links = extract_links(BeautifulSoup(html, "lxml"), url)
                classification = classify_page(url, html, links)
                page = DiscoveredPage(url, html, depth, path, classification, links)
                pages.append(page)
                self._update_stats(stats, classification.page_type)
                logger.info(
                    "[CLASSIFIER] %s -> %s confidence=%.2f",
                    url,
                    classification.page_type,
                    classification.confidence,
                )
                for link in links:
                    link.score = score_url(link)
                    if link.url in visited or link.url in queued or depth >= self.config.max_depth:
                        continue
                    if self.config.same_domain_only and self._host(link.url) != root_host:
                        continue
                    queued.add(link.url)
                    sequence += 1
                    child_path = [*path, link.url]
                    heapq.heappush(queue, (-link.score, depth + 1, sequence, link.url, child_path))
                stats.pages_discovered = len(queued)
                self._report(stats)
            except Exception:
                stats.errors += 1
                logger.exception("[CRAWLER] Failed to process %s", url)
                self._report(stats)
        return pages, stats

    @staticmethod
    def _host(url: str) -> str:
        return (urlsplit(url).hostname or "").lower().removeprefix("www.")

    @staticmethod
    def _needs_rendering(html: str, links: list) -> bool:
        text = BeautifulSoup(html, "lxml").get_text(" ").strip()
        return len(text) < 120 or not links

    @staticmethod
    def _update_stats(stats: CrawlStats, page_type: PageType) -> None:
        if page_type == PageType.TENDER_LIST:
            stats.tender_pages_found += 1
            stats.tender_list_pages += 1
        elif page_type == PageType.TENDER_DETAIL:
            stats.tender_pages_found += 1
            stats.tender_detail_pages += 1
        elif page_type == PageType.NEWS:
            stats.news_pages_found += 1
        else:
            stats.other_pages_found += 1

    def _report(self, stats: CrawlStats) -> None:
        if self.progress_callback:
            self.progress_callback(stats)
