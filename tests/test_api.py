from datetime import date

from app.models.models import Certificate


def payload():
    return {
        "title": "Python Workshop",
        "recipients": [
            {
                "name": "Karan Raj",
                "email": "karan@example.com",
                "course": "Python Backend Workshop",
                "completion_date": "2026-10-10",
            },
            {
                "name": "Rahul Kumar",
                "email": "rahul@example.com",
                "course": "Python Backend Workshop",
                "completion_date": "2026-10-10",
            },
        ],
    }


def test_create_generation_job(client):
    response = client.post("/api/jobs", json=payload())

    assert response.status_code == 202
    data = response.json()
    assert data["total_count"] == 2
    assert data["status"] == "COMPLETED"
    assert data["success_count"] == 2
    assert data["failure_count"] == 0


def test_input_validation(client):
    bad_payload = {
        "title": "",
        "recipients": [
            {
                "name": "A",
                "email": "not-an-email",
                "course": "",
                "completion_date": "2026-10-10",
            }
        ],
    }

    response = client.post("/api/jobs", json=bad_payload)
    assert response.status_code == 422


def test_job_status(client):
    create = client.post("/api/jobs", json=payload())
    job_id = create.json()["id"]

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["progress_percent"] == 100.0
    assert data["status"] == "COMPLETED"


def test_certificate_generation_and_retrieval(client):
    create = client.post("/api/jobs", json=payload())
    job_id = create.json()["id"]

    certificates = client.get(f"/api/jobs/{job_id}/certificates")
    assert certificates.status_code == 200

    data = certificates.json()
    assert len(data) == 2
    assert all(item["status"] == "COMPLETED" for item in data)

    certificate_id = data[0]["id"]
    download = client.get(f"/api/certificates/{certificate_id}/download")

    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_individual_certificate_failure_does_not_stop_other_generation(
    client, monkeypatch
):
    from app.services import generator

    original = generator.generate_certificate
    calls = {"count": 0}

    def flaky_generator(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("Simulated PDF generation failure")
        return original(**kwargs)

    monkeypatch.setattr(generator, "generate_certificate", flaky_generator)

    response = client.post("/api/jobs", json=payload())

    assert response.status_code == 202
    data = response.json()

    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["success_count"] == 1
    assert data["failure_count"] == 1

    job_id = data["id"]
    certificates = client.get(f"/api/jobs/{job_id}/certificates").json()

    assert certificates[0]["status"] == "FAILED"
    assert certificates[1]["status"] == "COMPLETED"
