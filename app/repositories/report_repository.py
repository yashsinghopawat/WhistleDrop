from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.status_update import StatusUpdate


def create_report(db: Session, case_code_hash: str, category: str, description: str,
                  evidence_url: str | None) -> Report:
    report = Report(
        case_code_hash=case_code_hash,
        category=category,
        description=description,
        evidence_url=evidence_url,
        status="SUBMITTED",
    )
    # first entry of the history, so the reporter sees that it was received
    report.updates.append(StatusUpdate(status="SUBMITTED", message="Report received"))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_by_case_code_hash(db: Session, case_code_hash: str) -> Report | None:
    return db.scalar(select(Report).where(Report.case_code_hash == case_code_hash))


def get_by_id(db: Session, report_id: int) -> Report | None:
    return db.get(Report, report_id)


def list_reports(db: Session, category: str | None, status: str | None, search: str | None,
                 skip: int, limit: int) -> list[Report]:
    query = select(Report)
    if category:
        query = query.where(Report.category == category)
    if status:
        query = query.where(Report.status == status)
    if search:
        like = f"%{search}%"
        query = query.where(or_(Report.description.ilike(like), Report.evidence_url.ilike(like)))
    query = query.order_by(Report.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def add_status_update(db: Session, report: Report, new_status: str, message: str | None) -> Report:
    report.status = new_status
    report.updates.append(StatusUpdate(status=new_status, message=message))
    db.commit()
    db.refresh(report)
    return report


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(select(Report.status, func.count()).group_by(Report.status)).all()
    return {status: count for status, count in rows}


def count_by_category(db: Session) -> dict[str, int]:
    rows = db.execute(select(Report.category, func.count()).group_by(Report.category)).all()
    return {category: count for category, count in rows}
