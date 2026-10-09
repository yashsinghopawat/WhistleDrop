from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_case_code, hash_case_code
from app.models.enums import ALLOWED_STATUS_CHANGES, Category, ReportStatus
from app.models.report import Report
from app.repositories import report_repository
from app.schemas.report import (
    AddUpdateRequest,
    ReportCreate,
    ReportStats,
    StatusChangeRequest,
)


def submit_report(db: Session, data: ReportCreate) -> tuple[str, Report]:
    case_code = generate_case_code()
    evidence_url = str(data.evidence_url) if data.evidence_url else None

    report = report_repository.create_report(
        db,
        case_code_hash=hash_case_code(case_code),
        category=data.category.value,
        description=data.description,
        evidence_url=evidence_url,
    )
    # the plain case code is returned only now, it is never stored
    return case_code, report


def track_report(db: Session, case_code: str) -> Report:
    report = report_repository.get_by_case_code_hash(db, hash_case_code(case_code))
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No report found for this case code")
    return report


def get_report_or_404(db: Session, report_id: int) -> Report:
    report = report_repository.get_by_id(db, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return report


def list_reports(db: Session, category: Category | None, report_status: ReportStatus | None,
                 search: str | None, skip: int, limit: int) -> list[Report]:
    return report_repository.list_reports(
        db,
        category=category.value if category else None,
        status=report_status.value if report_status else None,
        search=search.strip() if search else None,
        skip=skip,
        limit=limit,
    )


def change_status(db: Session, report_id: int, data: StatusChangeRequest) -> Report:
    report = get_report_or_404(db, report_id)
    current = ReportStatus(report.status)

    if not ALLOWED_STATUS_CHANGES[current]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This case is closed ({current.value}) and cannot be changed",
        )

    if data.status not in ALLOWED_STATUS_CHANGES[current]:
        allowed = ", ".join(s.value for s in ALLOWED_STATUS_CHANGES[current])
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot change status from {current.value} to {data.status.value}. Allowed: {allowed}",
        )

    return report_repository.add_status_update(db, report, data.status.value, data.message)


def add_update(db: Session, report_id: int, data: AddUpdateRequest) -> Report:
    report = get_report_or_404(db, report_id)

    if not ALLOWED_STATUS_CHANGES[ReportStatus(report.status)]:
        raise HTTPException(status.HTTP_409_CONFLICT, "This case is closed, no more updates allowed")

    # status stays the same, only a message is added to the history
    return report_repository.add_status_update(db, report, report.status, data.message)


def get_stats(db: Session) -> ReportStats:
    by_status = report_repository.count_by_status(db)
    by_category = report_repository.count_by_category(db)
    return ReportStats(total=sum(by_status.values()), by_status=by_status, by_category=by_category)
