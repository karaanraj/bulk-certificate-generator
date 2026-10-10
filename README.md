# Bulk Certificate Generator

A FastAPI backend that accepts a list of recipients, generates PDF certificates from one predefined template, tracks job progress, isolates individual failures, and provides certificate downloads.

## Why this architecture?

The API is intentionally separated into:

- **API layer** — HTTP endpoints and request/response handling.
- **Database layer** — SQLAlchemy models for jobs and certificates.
- **Service layer** — certificate generation and bulk processing.
- **Storage layer** — generated PDF files.

For this take-home, processing is implemented synchronously inside a dedicated service function. This keeps the project easy to run and explain without requiring Redis/Celery. The endpoint still returns `202 Accepted` to model the job-oriented API contract; a production version should enqueue the job before returning.

The service boundary makes it straightforward to move `process_job()` into a worker later if certificate generation becomes CPU-heavy or jobs become very large.

## Features

- FastAPI REST API
- Relational database via SQLAlchemy
- Bulk generation in one API request
- Pydantic input validation
- PDF generation using ReportLab
- Job-level status and progress
- Per-certificate status
- Individual failure isolation
- Certificate download endpoint
- Automated tests
- Docker support

## Requirements

- Python 3.11+
- pip

## Setup

```bash
git clone <your-repository-url>
cd bulk-certificate-generator

python -m venv .venv
```

Activate the virtual environment:

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

SQLite is used by default and the database file is created automatically.

## API

### 1. Create a generation job

```http
POST /api/jobs
Content-Type: application/json
```

Example:

```json
{
  "title": "Python Workshop",
  "recipients": [
    {
      "name": "Karan Raj",
      "email": "karan@example.com",
      "course": "Python Backend Workshop",
      "completion_date": "2026-10-10"
    },
    {
      "name": "Rahul Kumar",
      "email": "rahul@example.com",
      "course": "Python Backend Workshop",
      "completion_date": "2026-10-10"
    }
  ]
}
```

The API returns HTTP `202 Accepted`.

Example:

```json
{
  "id": "0b6c...",
  "title": "Python Workshop",
  "status": "COMPLETED",
  "total_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "created_at": "2026-10-10T10:00:00",
  "completed_at": "2026-10-10T10:00:01"
}
```

### 2. Get job status

```http
GET /api/jobs/{job_id}
```

Example response:

```json
{
  "id": "0b6c...",
  "title": "Python Workshop",
  "status": "COMPLETED_WITH_ERRORS",
  "total_count": 100,
  "success_count": 98,
  "failure_count": 2,
  "created_at": "2026-10-10T10:00:00",
  "completed_at": "2026-10-10T10:00:20",
  "progress_percent": 100.0
}
```

Possible statuses:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `COMPLETED_WITH_ERRORS`
- `FAILED`

### 3. List certificates for a job

```http
GET /api/jobs/{job_id}/certificates
```

Each certificate contains its individual status and error message, if any.

### 4. Download a certificate

```http
GET /api/certificates/{certificate_id}/download
```

A completed certificate is returned as a PDF.

## Failure handling

Each recipient is processed independently.

For example, if 100 recipients are submitted and certificate #37 fails:

- #37 is marked `FAILED`
- its error is stored
- the other 99 recipients continue
- the final job becomes `COMPLETED_WITH_ERRORS`

This satisfies the requirement that one bad certificate should not unnecessarily stop the whole bulk operation.

## Data model

### GenerationJob

Stores:

- job ID
- title
- total recipients
- successful count
- failed count
- job status
- timestamps

### Certificate

Stores:

- certificate ID
- job ID
- recipient details
- generation status
- generated filename
- error message

Relationship:

```text
GenerationJob 1 ──────── * Certificate
```

## Design decisions

### Why FastAPI?

FastAPI provides:

- simple REST API development
- automatic OpenAPI/Swagger documentation
- Pydantic validation
- clean dependency injection

### Why SQLAlchemy?

It keeps persistence independent from the HTTP layer and allows the default SQLite database to be replaced by PostgreSQL with minimal application changes.

### Why synchronous processing?

For this take-home, synchronous processing keeps setup simple and avoids requiring an external queue.

The generation code is isolated in `app/services/generator.py`, so it can later be moved to:

```text
API
 ↓
Database
 ↓
Queue (Redis/RabbitMQ/SQS)
 ↓
Worker
 ↓
Certificate Generator
 ↓
Object Storage (S3)
```

This would be preferable for very large jobs.

### Why ReportLab?

The certificate template is fixed, so ReportLab is sufficient and avoids introducing a template editor or browser-rendering dependency.

### Storage

Generated PDFs are stored locally under:

```text
storage/generated/
```

For production, this should be replaced with object storage such as Amazon S3, while the database stores the object key.

## Testing

Run:

```bash
pytest -q
```

Tests cover:

- creating a generation job
- input validation
- certificate generation
- job status/progress
- individual certificate failure
- retrieving/downloading generated certificates

## Docker

Build:

```bash
docker build -t bulk-certificate-generator .
```

Run:

```bash
docker run -p 8000:8000 bulk-certificate-generator
```

## Learning

This project was built to practice backend API design, relational data modelling, validation, file generation, error isolation, testing, and service-layer architecture.

## Future scope

For a production-scale version:

1. Use Celery/RQ/SQS for asynchronous job processing.
2. Use PostgreSQL instead of SQLite.
3. Store generated certificates in S3/object storage.
4. Add authentication and authorization.
5. Add idempotency keys for job creation.
6. Add retry policies for transient generation failures.
7. Add pagination for large certificate lists.
8. Add structured logging and metrics.
9. Add job cancellation.
10. Add rate limiting and upload/request size limits.


## Interview talking points

A few design decisions worth being able to explain:

1. **Why a job model?** A bulk request represents one unit of work and gives the client a stable ID for tracking.
2. **Why separate Certificate records?** Each recipient has an independent lifecycle and failure state.
3. **Why isolate failures?** A single malformed or failed certificate should not discard successful work.
4. **Why a service layer?** Certificate generation and job orchestration should not be coupled to HTTP routes.
5. **How would you scale it?** Put jobs on a queue, run multiple workers, store PDFs in object storage, and keep progress in PostgreSQL.
6. **How would you make retries safe?** Give each certificate a stable ID/idempotency key and only regenerate missing/failed outputs.
