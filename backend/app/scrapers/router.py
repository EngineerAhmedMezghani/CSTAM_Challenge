from app.scrapers.base import BaseScraper
from app.scrapers.adapters.appeloffres_net import AppelOffresNetScraper
from app.scrapers.adapters.marchespublics_tn import MarchesPublicsTnScraper
from app.scrapers.generic_extractor import GenericExtractor


def get_scraper(url: str) -> BaseScraper:
    if AppelOffresNetScraper.supports(url):
        return AppelOffresNetScraper()
    if MarchesPublicsTnScraper.supports(url):
        return MarchesPublicsTnScraper()
    return GenericExtractor()
