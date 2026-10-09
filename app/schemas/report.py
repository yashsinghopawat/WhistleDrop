from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.enums import Category, ReportStatus


class ReportCreate(BaseModel):
    category: Category
    description: str = Field(min_length=10, max_length=5000)
    evidence_url: HttpUrl | None = Field(default=None, description="Optional link to evidence")

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise ValueError("Description must have at least 10 characters")
        return value

    @field_validator("evidence_url")
    @classmethod
    def evidence_url_not_too_long(cls, value):
        # the database column is 500 characters
        if value is not None and len(str(value)) > 500:
            raise ValueError("Evidence URL is too long (max 500 characters)")
        return value


class TrackRequest(BaseModel):
    case_code: str = Field(min_length=1, max_length=50)


class ReportCreatedResponse(BaseModel):
    case_code: str
    status: ReportStatus
    message: str


class StatusUpdateResponse(BaseModel):
    status: ReportStatus
    message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# What the reporter gets back when tracking.
class ReportTrackResponse(BaseModel):
    category: Category
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    updates: list[StatusUpdateResponse]

    model_config = ConfigDict(from_attributes=True)


# Moderator views. There is no reporter field anywhere.
class ReportListItem(BaseModel):
    id: int
    category: Category
    status: ReportStatus
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetail(ReportListItem):
    evidence_url: str | None
    updated_at: datetime
    updates: list[StatusUpdateResponse]


class StatusChangeRequest(BaseModel):
    status: ReportStatus
    message: str | None = Field(default=None, max_length=300, description="Short update for the reporter")


class AddUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=300, description="Short update for the reporter")


class ReportStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
