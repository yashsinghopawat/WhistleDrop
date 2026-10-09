from enum import Enum


class Category(str, Enum):
    SECURITY = "SECURITY"
    HARASSMENT = "HARASSMENT"
    CORRUPTION = "CORRUPTION"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


# Which status can move to which. RESOLVED and DISMISSED are final,
# so a closed case can never be reopened.
ALLOWED_STATUS_CHANGES = {
    ReportStatus.SUBMITTED: [ReportStatus.UNDER_REVIEW],
    ReportStatus.UNDER_REVIEW: [ReportStatus.RESOLVED, ReportStatus.DISMISSED],
    ReportStatus.RESOLVED: [],
    ReportStatus.DISMISSED: [],
}
