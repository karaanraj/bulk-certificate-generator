from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.services.storage import certificate_path


def generate_certificate(
    *,
    certificate_id: str,
    name: str,
    course: str,
    completion_date: str,
) -> str:
    file_name = f"certificate_{certificate_id}.pdf"
    output = certificate_path(file_name)

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(output), pagesize=(page_width, page_height))

    # Simple predefined certificate template.
    pdf.setLineWidth(3)
    pdf.rect(35, 35, page_width - 70, page_height - 70)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 130,
        "CERTIFICATE OF COMPLETION",
    )

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 175,
        "This certificate is proudly presented to",
    )

    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 230,
        name,
    )

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 275,
        "for successfully completing",
    )

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 315,
        course,
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        page_width / 2,
        105,
        f"Completion Date: {completion_date}",
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        page_width / 2,
        75,
        f"Certificate ID: {certificate_id}",
    )

    pdf.save()
    return file_name
