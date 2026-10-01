import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.discovery.crawler import CrawlConfig
from app.discovery.models import CrawlStats
from app.discovery.source import GenericWebSource
from app.models.scrape_job import JobStage, JobStatus, ScrapeJob
from app.models.tender import Tender
from app.schemas.scrape_job import ScrapeAcceptedResponse, ScrapeJobCreate, ScrapeJobResponse
from app.scrapers.normalization import content_hash
from app.scrapers.generic_extractor import GenericExtractor
from app.scrapers.router import get_scraper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scrape", tags=["scrape"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_scrape_job(job_id: UUID) -> None:
    db = SessionLocal()
    try:
        job = db.get(ScrapeJob, job_id)
        if job is None:
            logger.error("Scrape job disappeared", extra={"job_id": str(job_id)})
            return
        job.status = JobStatus.RUNNING.value
        job.current_stage = JobStage.DISCOVERY.value
        job.started_at = _now()
        db.commit()
        logger.info("Scrape started", extra={"job_id": str(job_id), "url": job.input_url})

        scraper = get_scraper(job.input_url)
        logger.info("Selected scraper", extra={"job_id": str(job_id), "scraper": scraper.__class__.__name__})
        def report(stats: CrawlStats) -> None:
            job.current_stage = JobStage.CRAWLING.value
            job.pages_visited = stats.pages_visited
            job.pages_discovered = stats.pages_discovered
            job.tender_pages_found = stats.tender_pages_found
            db.commit()

        if isinstance(scraper, GenericExtractor):
            source = GenericWebSource(
                scraper,
                CrawlConfig(max_depth=job.max_depth, max_pages=job.max_pages),
                report,
            )
            extracted, _ = source.discover_and_extract(job.input_url)
        else:
            # A site adapter owns its discovery and extraction strategy. Running
            # the generic crawler first can produce false positives from listing
            # rows and prevent the adapter from ever being called.
            job.current_stage = JobStage.CRAWLING.value
            db.commit()
            extracted = scraper.scrape(job.input_url)
        job.current_stage = JobStage.EXTRACTION.value
        job.tenders_extracted = len(extracted)
        db.commit()
        logger.info("Number of tenders extracted", extra={"job_id": str(job_id), "count": len(extracted)})

        inserted = 0
        updated = 0
        seen_hashes: set[str] = set()
        for tender_data in extracted:
            job.current_stage = JobStage.DEDUPLICATION.value
            tender_hash = content_hash(tender_data)
            if tender_hash in seen_hashes:
                logger.info("Duplicate tender skipped", extra={"job_id": str(job_id), "content_hash": tender_hash})
                continue
            seen_hashes.add(tender_hash)
            existing = db.scalar(select(Tender).where(Tender.content_hash == tender_hash).limit(1))
            if existing:
                existing.job_id = job.id
                existing.source_url = tender_data.source_url
                existing.title = tender_data.title
                existing.description = tender_data.description
                existing.owner = tender_data.owner
                existing.contact = tender_data.contact
                existing.published_date = tender_data.published_date
                existing.deadline = tender_data.deadline
                existing.documents = tender_data.documents
                existing.raw_html_snippet = tender_data.raw_html_snippet
                existing.extraction_method = tender_data.extraction_method
                existing.page_type = tender_data.page_type
                existing.confidence_score = tender_data.confidence_score
                existing.confidence_signals = tender_data.confidence_signals
                existing.discovery_url = tender_data.discovery_url
                existing.discovery_depth = tender_data.discovery_depth
                existing.discovery_path = tender_data.discovery_path
                updated += 1
                logger.info("Duplicate tender updated", extra={"job_id": str(job_id), "content_hash": tender_hash})
                continue
            db.add(
                Tender(
                    job_id=job.id,
                    source_url=tender_data.source_url,
                    title=tender_data.title,
                    description=tender_data.description,
                    owner=tender_data.owner,
                    contact=tender_data.contact,
                    published_date=tender_data.published_date,
                    deadline=tender_data.deadline,
                    documents=tender_data.documents,
                    raw_html_snippet=tender_data.raw_html_snippet,
                    extraction_method=tender_data.extraction_method,
                    content_hash=tender_hash,
                    page_type=tender_data.page_type,
                    confidence_score=tender_data.confidence_score,
                    confidence_signals=tender_data.confidence_signals,
                    discovery_url=tender_data.discovery_url,
                    discovery_depth=tender_data.discovery_depth,
                    discovery_path=tender_data.discovery_path,
                )
            )
            inserted += 1
        job.status = JobStatus.DONE.value
        job.current_stage = JobStage.COMPLETED.value
        job.finished_at = _now()
        db.commit()
        logger.info("Scrape completed", extra={"job_id": str(job_id), "inserted": inserted, "updated": updated})
    except Exception as exc:
        db.rollback()
        logger.exception("Scrape failed", extra={"job_id": str(job_id)})
        failed_job = db.get(ScrapeJob, job_id)
        if failed_job:
            failed_job.status = JobStatus.FAILED.value
            failed_job.error_message = str(exc)[:2000]
            failed_job.finished_at = _now()
            db.commit()
    finally:
        db.close()


@router.post("", response_model=ScrapeAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_scrape_job(
    payload: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ScrapeAcceptedResponse:
    job = ScrapeJob(
        input_url=str(payload.url),
        status=JobStatus.PENDING.value,
        max_depth=payload.max_depth,
        max_pages=payload.max_pages,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("URL received", extra={"job_id": str(job.id), "url": job.input_url})
    background_tasks.add_task(run_scrape_job, job.id)
    return ScrapeAcceptedResponse(job_id=job.id, status=JobStatus.PENDING)


@router.get("/{job_id}", response_model=ScrapeJobResponse)
def get_scrape_job(job_id: UUID, db: Session = Depends(get_db)) -> ScrapeJob:
    job = db.get(ScrapeJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job
