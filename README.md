# CertFlow: Bulk Certificate Generator

Full-stack implementation of the Bulk Certificate Generator engineering assignment. It accepts one bulk request containing certificate metadata and many recipients, validates the data, creates a persistent generation job, generates one PDF per recipient in the background, tracks each result independently, and provides individual PDF and ZIP downloads.

## Features

- FastAPI REST API with Swagger/OpenAPI
- React + TypeScript dashboard
- Manual recipient entry and CSV import
- Quoted CSV fields supported
- Server-side Pydantic validation
- Duplicate-email protection
- Up to 5,000 recipients per job
- SQLAlchemy relational persistence
- SQLite by default, PostgreSQL-compatible model design
- Fixed ReportLab certificate template
- Background bulk processing with per-recipient failure isolation
- Live progress polling
- Individual PDF retrieval and bulk ZIP download
- Docker + Docker Compose
- Pytest integration tests
- GitHub Actions backend CI

## Architecture

```
React UI
   |
   | POST /api/v1/jobs
   v
FastAPI -> SQLAlchemy -> SQLite/PostgreSQL
   |
   | 202 Accepted + job ID
   v
Background processor
   |
   +-> recipient A -> PDF -> completed
   +-> recipient B -> PDF -> completed
   +-> recipient C -> error -> failed
   +-> recipient D -> PDF -> completed
   |
   v
File storage -> individual PDFs / ZIP archive
```

A bulk request is a **job**. Each recipient is an independently tracked work item, so one failed PDF does not stop the remaining recipients.

## Stack

**Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, ReportLab, Uvicorn, Pytest.

**Frontend:** React 18, TypeScript, Vite, Lucide React, CSS.

**Infrastructure:** Docker, Docker Compose, Nginx, GitHub Actions.

## Run locally

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Git

No API key, Redis instance, or PostgreSQL server is required for the assignment version.

### Backend

Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

URLs:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

Default frontend environment:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Environment

Backend `.env`:

```env
DATABASE_URL=sqlite:///./certificate_generator.db
CORS_ORIGINS=http://localhost:5173
MAX_RECIPIENTS=5000
STORAGE_DIR=./storage
```

Frontend `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## API

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/jobs` | List recent jobs |
| POST | `/jobs` | Create bulk generation job |
| GET | `/jobs/{job_id}` | Job progress + per-recipient results |
| GET | `/certificates/{id}` | Certificate metadata |
| GET | `/certificates/{id}/download` | Download one PDF |
| GET | `/jobs/{job_id}/download-all` | Download ZIP of successful PDFs |

Example POST:

```json
{
  "certificate": {
    "title": "Certificate of Completion",
    "event_name": "FastAPI Backend Workshop",
    "issuer_name": "Aereo Engineering Team",
    "issue_date": "2026-10-07"
  },
  "recipients": [
    {
      "name": "Aarav Sharma",
      "email": "aarav@example.com",
      "designation": "Software Intern",
      "organization": "Example Labs"
    },
    {
      "name": "Priya Singh",
      "email": "priya@example.com"
    }
  ]
}
```

The POST returns `202 Accepted` and a job ID.

## Validation

The backend is the final validation boundary:

- 1-5,000 recipients
- name: 2-120 characters
- valid email
- designation/organization optional, max 160 characters
- title: 5-120 characters
- event: 2-200 characters
- issuer: 2-160 characters
- valid issue date
- duplicate emails rejected inside one job

## CSV import

Example:

```csv
name,email,designation,organization
Aarav Sharma,aarav@example.com,Software Intern,Example Labs
Priya Singh,priya@example.com,Data Analyst,"Example, Inc."
```

Supported aliases include `name/full_name/recipient_name`, `email/recipient_email`, `designation/role`, and `organization/company`. The UI includes a sample CSV download and supports quoted fields containing commas.

## Certificate generation

The assignment requires one predefined design. ReportLab generates a landscape A4 PDF containing the title, recipient, event, designation, organization, issuer, issue date, certificate ID, and fixed decorative layout.

Dynamic user text is XML-escaped before ReportLab markup is rendered, preventing characters such as `<`, `>` and `&` from breaking generation.

## Job lifecycle

```
Job:         queued -> processing -> completed
                              \-> completed_with_errors

Certificate: pending -> processing -> completed
                              \-> failed
```

Each recipient is processed independently. A failed certificate is recorded and the next recipient continues.

## Why background processing?

A bulk job may contain hundreds or thousands of recipients. Generating every PDF inside the POST request would increase latency and timeout risk. The API persists the job, returns `202`, and processes recipients while the UI polls the job endpoint.

For production with multiple application instances, replace FastAPI BackgroundTasks with a durable worker queue such as Celery/RQ + Redis or another managed job system.

## Why SQLite?

SQLite provides a real relational database with zero setup. SQLAlchemy keeps the model portable to PostgreSQL. PostgreSQL is recommended for production.

## Storage

```text
storage/
  <job-id>/recipient_CERT-....pdf
  archives/certificates-<job-id>.zip
```

For production, use S3-compatible object storage and store object keys rather than local filesystem paths.

## Tests

Run:

```bash
cd backend
pytest -q
```

The suite covers health, duplicate validation, job creation, PDF generation/retrieval, ZIP generation, certificate metadata, special characters, and individual failure isolation.

Expected result:

```text
6 passed
```

## Docker

From the repository root:

```bash
docker compose up --build
```

Open http://localhost:5173.

Stop with `docker compose down`. Use `docker compose down -v` for a completely clean database/storage volume.

## CI

`.github/workflows/ci.yml` installs Python 3.12, installs backend dependencies and runs `pytest -q` for pushes and pull requests to `main`.

## Interview design decisions

**Why 202?** The POST creates a job instead of synchronously returning every PDF.

**Why job + certificate tables?** The job represents the bulk operation; certificate rows represent individual work units and make partial failure observable.

**Why independent commits?** One recipient failure must not roll back successful recipients.

**Why ReportLab?** The assignment needs one fixed design. ReportLab generates deterministic PDFs directly from Python without browser automation.

**Why FastAPI?** Typed schemas, Pydantic validation, automatic OpenAPI docs and a small readable API surface.

**Production improvements:** PostgreSQL, durable workers, S3, authentication, Alembic migrations, rate limiting, idempotency keys, retry/backoff, structured logging/metrics, signed downloads, and frontend CI.

## Security

The implementation validates on the server, limits bulk size, rejects duplicate recipients, sanitizes filenames, escapes PDF text, exposes files only through known certificate records, keeps secrets out of source control, and configures CORS explicitly.

## Submission checklist

- [ ] Clone into a clean directory
- [ ] Install backend dependencies
- [ ] Install frontend dependencies
- [ ] Start backend + frontend
- [ ] Create a 2-3 recipient job
- [ ] Confirm progress reaches 100%
- [ ] Open a generated PDF
- [ ] Download the ZIP
- [ ] Test CSV import
- [ ] Run `pytest -q`
- [ ] Test invalid/duplicate input
- [ ] Inspect `/docs`
- [ ] Test Docker
- [ ] Verify GitHub Actions
