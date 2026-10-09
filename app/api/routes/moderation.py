from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.enums import Category, ReportStatus
from app.schemas.report import (
    AddUpdateRequest,
    ReportDetail,
    ReportListItem,
    ReportStats,
    StatusChangeRequest,
)
from app.services import report_service

router = APIRouter(
    prefix="/moderation/reports",
    tags=["Moderation"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ReportListItem])
def list_reports(
    category: Category | None = None,
    status: ReportStatus | None = None,
    search: str | None = Query(default=None, description="Text to look for in description or evidence URL"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List reports. Can be filtered by category, status or search text."""
    return report_service.list_reports(db, category, status, search, skip, limit)


# keep this above /{report_id}, otherwise "stats" would be read as an id
@router.get("/stats", response_model=ReportStats)
def report_stats(db: Session = Depends(get_db)):
    """Number of reports per status and per category."""
    return report_service.get_stats(db)


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    return report_service.get_report_or_404(db, report_id)


@router.patch("/{report_id}/status", response_model=ReportDetail)
def change_status(report_id: int, data: StatusChangeRequest, db: Session = Depends(get_db)):
    """Change the status. Flow: SUBMITTED -> UNDER_REVIEW -> RESOLVED or DISMISSED (final)."""
    return report_service.change_status(db, report_id, data)


@router.post("/{report_id}/updates", response_model=ReportDetail, status_code=201)
def add_update(report_id: int, data: AddUpdateRequest, db: Session = Depends(get_db)):
    """Add a short message for the reporter without changing the status."""
    return report_service.add_update(db, report_id, data)
