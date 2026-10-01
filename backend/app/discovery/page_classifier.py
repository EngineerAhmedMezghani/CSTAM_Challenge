import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from app.discovery.link_extractor import ascii_fold, extract_links
from app.discovery.models import LinkCandidate, PageClassification, PageType

_TENDER_TERMS = re.compile(r"appel\s+d['’ ]?offres|avis\s+d['’ ]?appel|cahier\s+des\s+charges|date\s+(limite|de\s+cloture)|soumission|procurement|\btender\b|\brfp\b", re.I)
_NEWS_TERMS = re.compile(r"actualit|news|nouvelle|communique|circulaire", re.I)
_EVENT_TERMS = re.compile(r"evenement|event|formation|webinaire|salon|workshop", re.I)
_REGULATION_TERMS = re.compile(r"legislation|reglement|loi|decret|reglementation|juridique", re.I)
_CONTACT_TERMS = re.compile(r"contact|connexion|login|faq", re.I)
_DETAIL_PATH = re.compile(
    r"/(?:appels[-_](?:d[-_]?)?offres?)/(?:tender[-_/])?[a-z0-9-]+/?$",
    re.I,
)
_LIST_PATH = re.compile(r"/(?:appels[-_](?:d[-_]?)?offres?)/?$", re.I)


def _page_text(soup: BeautifulSoup) -> str:
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return " ".join(soup.get_text(" ").split())


def classify_page(url: str, html: str, links: list[LinkCandidate] | None = None) -> PageClassification:
    soup = BeautifulSoup(html, "lxml")
    text = _page_text(soup)
    folded = ascii_fold(f"{url} {soup.title.get_text(' ') if soup.title else ''} {text}")
    links = links if links is not None else extract_links(soup, url)
    detail_links = [link for link in links if _DETAIL_PATH.search(urlsplit(link.url).path)]
    tender_keywords = bool(_TENDER_TERMS.search(text))
    deadline_found = bool(re.search(r"date\s+(limite|de\s+cloture)|deadline|closing", text, re.I))
    document_found = bool(soup.find("a", href=re.compile(r"\.(pdf|docx?|xlsx?|zip)(?:$|[?#])", re.I)))
    list_structure = len(detail_links) >= 2 or len(soup.select("article, .card, .tender, tbody tr")) >= 2
    detail_path = bool(_DETAIL_PATH.search(urlsplit(url).path))
    list_path = bool(_LIST_PATH.search(urlsplit(url).path))
    signals = {
        "tender_keywords": tender_keywords,
        "deadline_found": deadline_found,
        "document_found": document_found,
        "detail_path": detail_path,
        "list_path": list_path,
        "multiple_tender_links": len(detail_links) >= 2,
        "list_structure": list_structure,
    }
    tender_score = sum((0.25, 0.18, 0.12, 0.30, 0.25, 0.35, 0.20)[index] for index, value in enumerate(signals.values()) if value)
    tender_score = min(1.0, tender_score)
    if detail_path:
        return PageClassification(PageType.TENDER_DETAIL, max(0.85, tender_score), signals)
    if list_path or (list_structure and tender_keywords):
        return PageClassification(PageType.TENDER_LIST, max(0.80, tender_score), signals)
    if _EVENT_TERMS.search(folded):
        return PageClassification(PageType.EVENT, 0.86 if not tender_keywords else 0.62, signals)
    if _REGULATION_TERMS.search(folded):
        return PageClassification(PageType.REGULATION, 0.84, signals)
    if _CONTACT_TERMS.search(folded):
        return PageClassification(PageType.CONTACT, 0.82, signals)
    if _NEWS_TERMS.search(folded):
        return PageClassification(PageType.NEWS, 0.80, signals)
    if tender_score:
        return PageClassification(PageType.TENDER_DETAIL, min(0.78, tender_score), signals)
    return PageClassification(PageType.OTHER, 0.55, signals)
