from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Certificate

router = APIRouter(prefix="/certificates", tags=["certificates"])

@router.get("/{certificate_id}")
def get_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "id": cert.id,
        "recipient_name": cert.recipient_name,
        "recipient_email": cert.recipient_email,
        "status": cert.status,
        "certificate_code": cert.certificate_code,
        "error_message": cert.error_message,
        "download_url": f"/api/v1/certificates/{cert.id}/download" if cert.file_path else None,
    }

@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "completed" or not cert.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available yet")
    path = Path(cert.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Certificate file is missing")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
