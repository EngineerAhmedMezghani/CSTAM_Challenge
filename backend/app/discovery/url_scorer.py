import re

from app.discovery.link_extractor import link_text
from app.discovery.models import LinkCandidate

_POSITIVE = {
    "appel d offre": 38,
    "appel d offres": 42,
    "appels offres": 45,
    "appel offres": 42,
    "marches publics": 34,
    "procurement": 32,
    "tender": 32,
    "tenders": 35,
    "rfp": 28,
    "rfq": 28,
    "consultation": 20,
    "soumission": 22,
    "avis": 12,
}
_NEGATIVE = {
    "contact": 35,
    "login": 35,
    "connexion": 35,
    "privacy": 25,
    "cookies": 25,
    "mentions legales": 25,
    "a propos": 20,
    "about": 20,
}


def score_url(candidate: LinkCandidate) -> float:
    text = link_text(candidate)
    score = 0.0
    for keyword, weight in _POSITIVE.items():
        if keyword in text:
            score += weight
    for keyword, weight in _NEGATIVE.items():
        if keyword in text:
            score -= weight
    if re.search(r"/tender[-_/]?[a-z0-9]+", text):
        score += 35
    if re.search(r"/appels?[-_ ]doffres", text):
        score += 25
    return max(0.0, min(100.0, score))
