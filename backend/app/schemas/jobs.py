from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RecipientInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    designation: str | None = Field(default=None, max_length=160)
    organization: str | None = Field(default=None, max_length=160)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if len(value) < 2:
            raise ValueError("Recipient name must contain at least 2 characters")
        return value

class CertificateInfo(BaseModel):
    title: str = Field(default="Certificate of Completion", min_length=5, max_length=120)
    event_name: str = Field(min_length=2, max_length=200)
    issuer_name: str = Field(min_length=2, max_length=160)
    issue_date: date

class CreateJobRequest(BaseModel):
    certificate: CertificateInfo
    recipients: list[RecipientInput] = Field(min_length=1, max_length=5000)

class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    recipient_name: str
    recipient_email: str
    designation: str | None
    organization: str | None
    status: str
    certificate_code: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    download_url: str | None = None

class JobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    certificate_title: str
    event_name: str
    issuer_name: str
    issue_date: date
    total_count: int
    success_count: int
    failed_count: int
    status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

class JobDetail(JobSummary):
    certificates: list[CertificateResponse]
    progress_percent: float
