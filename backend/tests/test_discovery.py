from app.discovery.crawler import CrawlConfig, DiscoveryCrawler
from app.discovery.link_extractor import normalize_url
from app.discovery.models import PageType
from app.discovery.page_classifier import classify_page
from app.discovery.url_scorer import score_url
from app.discovery.models import LinkCandidate


def test_normalize_url_removes_fragments_tracking_and_trailing_slash():
    assert normalize_url("/fr/appels-doffres/?utm_source=test#top", "https://example.tn") == "https://example.tn/fr/appels-doffres"


def test_url_score_prefers_tender_links_over_contact():
    tender = LinkCandidate("https://example.tn/page/123", anchor_text="Avis d'appel d'offres")
    contact = LinkCandidate("https://example.tn/contact", anchor_text="Contact")
    assert score_url(tender) > score_url(contact)
    assert score_url(tender) >= 50


def test_page_classifier_detects_list_detail_news_and_event():
    listing = """
        <h1>Appels d'offres</h1>
        <a href='/fr/appels-doffres/Tender-1'>Appel d'offres A</a>
        <a href='/fr/appels-doffres/Tender-2'>Appel d'offres B</a>
    """
    detail = "<h1>Acquisition de serveurs</h1><p>Avis d'appel d'offres. Date limite: 2026-10-01</p><a href='/files/cahier.pdf'>Cahier</a>"
    news = "<h1>Actualités</h1><p>Le portail annonce une nouvelle initiative.</p>"
    event = "<h1>Webinaire sur les marchés publics</h1><p>Inscription à l'événement.</p>"
    assert classify_page("https://example.tn/fr/appels-doffres", listing).page_type == PageType.TENDER_LIST
    assert classify_page("https://example.tn/fr/appels-doffres/Tender-1", detail).page_type == PageType.TENDER_DETAIL
    assert classify_page("https://example.tn/fr/actualites", news).page_type == PageType.NEWS
    assert classify_page("https://example.tn/fr/evenements", event).page_type == PageType.EVENT


def test_crawler_respects_same_domain_depth_and_page_limits():
    pages = {
        "https://example.tn": "<a href='/fr/appels-doffres'>Appels d'offres</a><a href='https://external.test/x'>External</a>",
        "https://example.tn/fr/appels-doffres": "<a href='/fr/appels-doffres/Tender-1'>Tender 1</a>",
        "https://example.tn/fr/appels-doffres/Tender-1": "<h1>Tender 1</h1><p>Avis d'appel d'offres Date limite: 2026-10-01</p>",
    }
    crawler = DiscoveryCrawler(lambda url: pages[url], CrawlConfig(max_depth=1, max_pages=10))
    discovered, stats = crawler.crawl("https://example.tn")
    assert [page.url for page in discovered] == ["https://example.tn", "https://example.tn/fr/appels-doffres"]
    assert stats.pages_visited == 2


def test_crawler_honors_max_pages():
    pages = {
        "https://example.tn": "<a href='/a'>A</a><a href='/b'>B</a>",
        "https://example.tn/a": "<p>A</p>",
        "https://example.tn/b": "<p>B</p>",
    }
    crawler = DiscoveryCrawler(lambda url: pages[url], CrawlConfig(max_depth=3, max_pages=2))
    _, stats = crawler.crawl("https://example.tn")
    assert stats.pages_visited == 2
