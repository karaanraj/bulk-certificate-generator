from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Certificate, GenerationJob, JobStatus
from app.schemas.schemas import (
    CertificateResponse,
    JobCreateRequest,
    JobResponse,
    JobSummaryResponse,
)
from app.services.generator import process_job
from app.services.storage import certificate_path

router = APIRouter(tags=["Certificates"])


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_generation_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
):
    job = GenerationJob(
        title=payload.title,
        total_count=len(payload.recipients),
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.flush()

    for recipient in payload.recipients:
        certificate = Certificate(
            job_id=job.id,
            name=recipient.name,
            email=recipient.email,
            course=recipient.course,
            completion_date=recipient.completion_date,
            status="PENDING",
        )
        db.add(certificate)

    db.commit()
    db.refresh(job)

    # Deliberately process synchronously for this take-home:
    # it keeps the project self-contained without requiring Redis/Celery.
    # The service layer is isolated so it can later be moved to a worker.
    process_job(job.id)

    db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=JobSummaryResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    progress = (
        100.0
        if job.total_count == 0
        else round(
            ((job.success_count + job.failure_count) / job.total_count) * 100,
            2,
        )
    )

    return JobSummaryResponse(
        id=job.id,
        title=job.title,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        created_at=job.created_at,
        completed_at=job.completed_at,
        progress_percent=progress,
    )


@router.get("/jobs/{job_id}/certificates", response_model=List[CertificateResponse])
def list_certificates(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    return (
        db.query(Certificate)
        .filter(Certificate.job_id == job.id)
        .order_by(Certificate.created_at.asc())
        .all()
    )


@router.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    certificate = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id)
        .first()
    )
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if certificate.status != "COMPLETED" or not certificate.file_name:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available for download",
        )

    path = certificate_path(certificate.file_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated file not found")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=certificate.file_name,
    )
