from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.models import JobStatus


class RecipientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    course: str = Field(min_length=2, max_length=200)
    completion_date: date

    @field_validator("name", "course")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    recipients: List[RecipientCreate] = Field(min_length=1, max_length=5000)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be blank")
        return value


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    course: str
    completion_date: date
    status: str
    file_name: str | None = None
    error_message: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: JobStatus
    total_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    completed_at: datetime | None = None


class JobSummaryResponse(JobResponse):
    progress_percent: float
