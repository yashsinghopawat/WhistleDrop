from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.report import (
    ReportCreate,
    ReportCreatedResponse,
    ReportTrackResponse,
    TrackRequest,
)
from app.services import report_service

# Public endpoints, no login needed
router = APIRouter(prefix="/reports", tags=["Anonymous Reporting"])


@router.post("", response_model=ReportCreatedResponse, status_code=status.HTTP_201_CREATED)
def submit_report(data: ReportCreate, db: Session = Depends(get_db)):

    """Submit a report without an account. The case code is shown only once, so save it."""
    
    case_code, report = report_service.submit_report(db, data)
    return ReportCreatedResponse(
        case_code=case_code,
        status=report.status,
        message="Report submitted. Save your case code, it cannot be recovered.",
    )


@router.post("/track", response_model=ReportTrackResponse)
def track_report(data: TrackRequest, db: Session = Depends(get_db)):
    
    return report_service.track_report(db, data.case_code)
