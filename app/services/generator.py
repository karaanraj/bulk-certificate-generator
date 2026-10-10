from datetime import datetime
from pathlib import Path

from app.db.database import SessionLocal
from app.models.models import Certificate, GenerationJob, JobStatus
from app.services.certificate import generate_certificate


def process_job(job_id: str) -> None:
    """
    Generate every certificate independently.

    A failure for one recipient is recorded on that certificate and does not
    stop the remaining recipients from being processed.
    """
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job.id)
            .order_by(Certificate.created_at.asc())
            .all()
        )

        success_count = 0
        failure_count = 0

        for certificate in certificates:
            try:
                certificate.status = "PROCESSING"
                db.commit()

                file_name = generate_certificate(
                    certificate_id=str(certificate.id),
                    name=certificate.name,
                    course=certificate.course,
                    completion_date=certificate.completion_date.isoformat(),
                )

                certificate.file_name = file_name
                certificate.status = "COMPLETED"
                certificate.error_message = None
                success_count += 1

            except Exception as exc:
                certificate.status = "FAILED"
                certificate.error_message = str(exc)
                failure_count += 1

            db.commit()

        job.success_count = success_count
        job.failure_count = failure_count
        job.completed_at = datetime.utcnow()

        if success_count == job.total_count:
            job.status = JobStatus.COMPLETED
        elif success_count > 0:
            job.status = JobStatus.COMPLETED_WITH_ERRORS
        else:
            job.status = JobStatus.FAILED

        db.commit()

    except Exception as exc:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
