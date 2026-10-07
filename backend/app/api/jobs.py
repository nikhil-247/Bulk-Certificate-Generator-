import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Certificate, GenerationJob
from app.schemas.jobs import CertificateResponse, CreateJobRequest, JobDetail, JobSummary
from app.services.job_processor import process_job

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()

def _certificate_response(cert: Certificate) -> CertificateResponse:
    return CertificateResponse(
        id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        designation=cert.designation,
        organization=cert.organization,
        status=cert.status,
        certificate_code=cert.certificate_code,
        error_message=cert.error_message,
        created_at=cert.created_at,
        completed_at=cert.completed_at,
        download_url=f"/api/v1/certificates/{cert.id}/download" if cert.file_path else None,
    )

@router.post("", response_model=JobSummary, status_code=202)
def create_job(payload: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    normalized = [str(r.email).strip().lower() for r in payload.recipients]
    if len(normalized) != len(set(normalized)):
        raise HTTPException(status_code=422, detail="Duplicate recipient email addresses are not allowed in the same job")

    job = GenerationJob(
        certificate_title=payload.certificate.title.strip(),
        event_name=payload.certificate.event_name.strip(),
        issuer_name=payload.certificate.issuer_name.strip(),
        issue_date=payload.certificate.issue_date,
        total_count=len(payload.recipients),
        status="queued",
    )
    db.add(job)
    db.flush()

    for recipient in payload.recipients:
        db.add(Certificate(
            job_id=job.id,
            recipient_name=recipient.name.strip(),
            recipient_email=str(recipient.email).lower(),
            designation=recipient.designation.strip() if recipient.designation else None,
            organization=recipient.organization.strip() if recipient.organization else None,
            status="pending",
            certificate_code=f"CERT-{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
        ))
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    return job

@router.get("", response_model=list[JobSummary])
def list_jobs(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    return db.scalars(select(GenerationJob).order_by(desc(GenerationJob.created_at)).limit(limit)).all()

@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    certs = db.scalars(select(Certificate).where(Certificate.job_id == job_id).order_by(Certificate.created_at)).all()
    processed = job.success_count + job.failed_count
    progress = round((processed / job.total_count) * 100, 2) if job.total_count else 0
    return JobDetail(**JobSummary.model_validate(job).model_dump(), certificates=[_certificate_response(c) for c in certs], progress_percent=progress)

@router.get("/{job_id}/download-all")
def download_all(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    certs = db.scalars(select(Certificate).where(Certificate.job_id == job_id, Certificate.file_path.is_not(None), Certificate.status == "completed")).all()
    if not certs:
        raise HTTPException(status_code=409, detail="No completed certificates are available yet")

    zip_dir = Path(settings.storage_dir) / "archives"
    zip_dir.mkdir(parents=True, exist_ok=True)
    archive = zip_dir / f"certificates-{job_id}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for cert in certs:
            path = Path(cert.file_path)
            if path.exists():
                zf.write(path, arcname=path.name)
    return FileResponse(archive, media_type="application/zip", filename=f"certificates-{job_id}.zip")
