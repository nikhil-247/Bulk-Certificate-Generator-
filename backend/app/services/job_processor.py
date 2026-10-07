from datetime import datetime, timezone
from pathlib import Path
import re
from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Certificate, GenerationJob
from app.services.certificate import CertificateGenerator

settings = get_settings()
generator = CertificateGenerator()

def _safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip()).strip("_")[:80] or "recipient"

def process_job(job_id: str) -> None:
    """Process each certificate independently so one failure does not stop the bulk job."""
    db = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        output_dir = Path(settings.storage_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        recipients = db.scalars(select(Certificate).where(Certificate.job_id == job_id).order_by(Certificate.created_at)).all()

        for cert in recipients:
            cert.status = "processing"
            db.commit()
            try:
                filename = f"{_safe_filename(cert.recipient_name)}_{cert.certificate_code}.pdf"
                path = output_dir / filename
                generator.generate(
                    path,
                    certificate_title=job.certificate_title,
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date.strftime("%d %B %Y"),
                    recipient_name=cert.recipient_name,
                    designation=cert.designation,
                    organization=cert.organization,
                    certificate_code=cert.certificate_code,
                )
                cert.status = "completed"
                cert.file_path = str(path)
                cert.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                job.success_count += 1
            except Exception as exc:
                cert.status = "failed"
                cert.error_message = str(exc)[:1000]
                cert.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                job.failed_count += 1
            db.commit()

        job.status = "completed" if job.failed_count == 0 else "completed_with_errors"
        job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
    except Exception as exc:
        job = db.get(GenerationJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
    finally:
        db.close()
