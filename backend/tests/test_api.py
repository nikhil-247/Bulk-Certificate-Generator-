from datetime import date
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def sample_payload():
    return {
        "certificate": {
            "title": "Certificate of Completion",
            "event_name": "Backend Engineering Workshop",
            "issuer_name": "Aereo Demo",
            "issue_date": str(date.today()),
        },
        "recipients": [
            {"name": "Aarav Sharma", "email": "aarav@example.com", "designation": "Engineer", "organization": "Aereo"},
            {"name": "Priya Singh", "email": "priya@example.com"},
        ],
    }

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_validation_rejects_invalid_recipient_email():
    payload = sample_payload()
    payload["recipients"][0]["email"] = "not-an-email"
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_validation_rejects_duplicate_emails():
    payload = sample_payload()
    payload["recipients"][1]["email"] = "AARAV@example.com"
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    assert "Duplicate recipient" in response.json()["detail"]

def test_bulk_job_generates_and_retrieves_certificates():
    response = client.post("/api/v1/jobs", json=sample_payload())
    assert response.status_code == 202
    job_id = response.json()["id"]

    detail = client.get(f"/api/v1/jobs/{job_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "completed"
    assert body["success_count"] == 2
    assert body["failed_count"] == 0
    assert body["progress_percent"] == 100.0
    assert all(item["status"] == "completed" for item in body["certificates"])

    pdf = client.get(body["certificates"][0]["download_url"])
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")

    archive = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert archive.status_code == 200
    assert archive.headers["content-type"].startswith("application/zip")

def test_single_certificate_failure_does_not_stop_other_certificates(monkeypatch):
    from app.services import job_processor
    original = job_processor.generator.generate

    def flaky_generate(output_path, **kwargs):
        if kwargs["recipient_name"] == "Aarav Sharma":
            raise RuntimeError("simulated template failure")
        return original(output_path, **kwargs)

    monkeypatch.setattr(job_processor.generator, "generate", flaky_generate)
    response = client.post("/api/v1/jobs", json=sample_payload())
    assert response.status_code == 202
    job_id = response.json()["id"]
    detail = client.get(f"/api/v1/jobs/{job_id}").json()

    assert detail["status"] == "completed_with_errors"
    assert detail["success_count"] == 1
    assert detail["failed_count"] == 1
    statuses = {item["recipient_name"]: item["status"] for item in detail["certificates"]}
    assert statuses["Aarav Sharma"] == "failed"
    assert statuses["Priya Singh"] == "completed"

def test_certificate_metadata_endpoint():
    response = client.post("/api/v1/jobs", json=sample_payload())
    assert response.status_code == 202
    job = response.json()
    detail = client.get(f"/api/v1/jobs/{job['id']}").json()
    certificate_id = detail["certificates"][0]["id"]

    metadata = client.get(f"/api/v1/certificates/{certificate_id}")
    assert metadata.status_code == 200
    assert metadata.json()["certificate_code"] == detail["certificates"][0]["certificate_code"]

def test_special_characters_are_safe_in_pdf_generation():
    payload = sample_payload()
    payload["certificate"]["event_name"] = "R&D <Backend> Workshop"
    payload["certificate"]["issuer_name"] = "Aereo & Partners"
    payload["recipients"][0]["name"] = "Aarav <Sharma> & Co"

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    detail = client.get(f"/api/v1/jobs/{response.json()['id']}").json()
    assert detail["status"] == "completed"
    assert detail["success_count"] == 2
