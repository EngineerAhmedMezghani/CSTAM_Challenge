import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urldefrag, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.discovery.models import LinkCandidate

_TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref"}


def normalize_url(url: str, base_url: str | None = None) -> str | None:
    absolute = urljoin(base_url or url, url)
    absolute, _ = urldefrag(absolute.strip())
    parsed = urlsplit(absolute)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    port = parsed.port
    netloc = hostname
    if port and not ((parsed.scheme.lower() == "http" and port == 80) or (parsed.scheme.lower() == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in _TRACKING_PARAMETERS and not key.lower().startswith("utm_")
        )
    )
    path = parsed.path or ""
    if path and path != "/":
        path = path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _context(anchor) -> str:
    parent = anchor.find_parent(["li", "article", "td", "div", "section"])
    return _clean_text(parent.get_text(" "))[:500] if parent else ""


def extract_links(soup: BeautifulSoup, page_url: str) -> list[LinkCandidate]:
    candidates: list[LinkCandidate] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", ""))
        if href.lower().startswith(("javascript:", "mailto:", "tel:", "data:", "#")):
            continue
        normalized = normalize_url(href, page_url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(
            LinkCandidate(
                url=normalized,
                anchor_text=_clean_text(anchor.get_text(" ")),
                title=_clean_text(anchor.get("title")),
                aria_label=_clean_text(anchor.get("aria-label")),
                context=_context(anchor),
            )
        )
    return candidates


def ascii_fold(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return folded.replace("'", " ")


def link_text(candidate: LinkCandidate) -> str:
    return ascii_fold(" ".join((candidate.url, candidate.anchor_text, candidate.title, candidate.aria_label, candidate.context)))


def compact_path(url: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", ascii_fold(url))
