from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tender import Tender
from app.schemas.tender import TenderListResponse

router = APIRouter(prefix="/api/tenders", tags=["tenders"])


@router.get("", response_model=TenderListResponse)
def list_tenders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    job_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> TenderListResponse:
    filters = [Tender.job_id == job_id] if job_id else []
    total = db.scalar(select(func.count(Tender.id)).where(*filters)) or 0
    items = db.scalars(
        select(Tender)
        .where(*filters)
        .order_by(Tender.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return TenderListResponse(items=items, total=total, page=page, page_size=page_size)
