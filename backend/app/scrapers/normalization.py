import hashlib
import re
from datetime import date

from app.scrapers.base import TenderData


def _normalize(value: str | date | None) -> str:
    if value is None:
        return ""
    text = value.isoformat() if isinstance(value, date) else value
    return re.sub(r"\s+", " ", text).strip().casefold()


def content_hash(tender: TenderData) -> str:
    stable_content = "\n".join(
        _normalize(value)
        for value in (tender.source_url, tender.title, tender.description, tender.published_date, tender.deadline)
    )
    return hashlib.sha256(stable_content.encode("utf-8")).hexdigest()
