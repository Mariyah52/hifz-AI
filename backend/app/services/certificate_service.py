from collections import defaultdict
from io import BytesIO

import httpx
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.lesson import Sabaq
from app.models.organization import Organization
from app.models.user import StudentProfile
from app.services.quran_text import get_ayah_positions, get_juz_ayahs, get_surah_list

"""
Two different kinds of "automatic" here, and the distinction matters:

- surah_completion / juz_completion are detected lazily — the same
  self-healing "check on every relevant GET" pattern Phase 15's
  achievements established, computed from real completed-Sabaq coverage
  (unioned ayah ranges checked against the real surah ayah count / real
  juz composition, both fetched live via quran_text.py — never a
  hand-typed lookup table).
- attendance and competition certificates require a human judgment call
  (which milestone, which standing) a teacher or admin makes explicitly
  — see issue_certificate(). Nothing here invents an attendance count or
  a competition result without a person deciding to issue it.

The PDF itself is rendered on demand (never stored) from this row's data
plus the organization's real branding — see render_certificate_pdf().
"Teacher signed" means the teacher's real name printed in a signature-
styled font on a signature line, not an uploaded/scanned signature image
or an e-signature flow — neither was built, stated plainly rather than
implied.
"""


def _covered_ayahs(sabaqs: list[Sabaq]) -> set[int]:
    covered: set[int] = set()
    for sabaq in sabaqs:
        covered.update(range(sabaq.from_ayah, sabaq.to_ayah + 1))
    return covered


def _create(
    db: Session, student_id: str, cert_type: str, title: str, detail: str, issued_by_teacher_id: str | None = None
) -> Certificate:
    cert = Certificate(
        student_id=student_id, type=cert_type, title=title, detail=detail, issued_by_teacher_id=issued_by_teacher_id
    )
    db.add(cert)
    return cert


async def check_and_award_certificates(db: Session, student: StudentProfile) -> list[Certificate]:
    completed_sabaqs = db.query(Sabaq).filter(Sabaq.student_id == student.id, Sabaq.status == "completed").all()
    if not completed_sabaqs:
        return []

    existing_titles = {c.title for c in db.query(Certificate).filter(Certificate.student_id == student.id).all()}
    newly_issued: list[Certificate] = []

    completed_by_surah: dict[int, list[Sabaq]] = defaultdict(list)
    for sabaq in completed_sabaqs:
        completed_by_surah[sabaq.surah_number].append(sabaq)

    try:
        surah_list = {s["number"]: s for s in await get_surah_list()}
    except Exception:
        surah_list = {}

    for surah_number, sabaqs in completed_by_surah.items():
        surah_meta = surah_list.get(surah_number)
        if not surah_meta:
            continue
        title = f"Surah {surah_meta['name']} \u2014 Completion"
        if title in existing_titles:
            continue
        if _covered_ayahs(sabaqs) >= set(range(1, surah_meta["ayah_count"] + 1)):
            newly_issued.append(
                _create(
                    db, student.id, "surah_completion", title,
                    f"Completed all {surah_meta['ayah_count']} ayahs of Surah {surah_meta['name']}.",
                )
            )
            existing_titles.add(title)

    positions_by_surah: dict[int, dict] = {}
    for surah_number in completed_by_surah:
        try:
            positions_by_surah[surah_number] = await get_ayah_positions(surah_number)
        except Exception:
            continue

    touched_juz: set[int] = set()
    for surah_number, sabaqs in completed_by_surah.items():
        positions = positions_by_surah.get(surah_number, {})
        for sabaq in sabaqs:
            for ayah in range(sabaq.from_ayah, sabaq.to_ayah + 1):
                juz = positions.get(ayah, {}).get("juz")
                if juz:
                    touched_juz.add(juz)

    for juz_number in touched_juz:
        title = f"Juz {juz_number} \u2014 Completion"
        if title in existing_titles:
            continue
        try:
            juz_ayahs = await get_juz_ayahs(juz_number)
        except Exception:
            continue
        fully_covered = all(
            any(s.surah_number == surah_number and s.from_ayah <= ayah_number <= s.to_ayah for s in completed_sabaqs)
            for surah_number, ayah_number in juz_ayahs
        )
        if fully_covered:
            newly_issued.append(
                _create(db, student.id, "juz_completion", title, f"Completed all ayahs of Juz {juz_number}.")
            )
            existing_titles.add(title)

    if newly_issued:
        db.commit()
        for cert in newly_issued:
            db.refresh(cert)
    return newly_issued


def issue_certificate(
    db: Session, student_id: str, cert_type: str, title: str, detail: str, issued_by_teacher_id: str
) -> Certificate:
    """For 'attendance' and 'competition' — types that need a teacher/admin's judgment, not auto-detection."""
    cert = _create(db, student_id, cert_type, title, detail, issued_by_teacher_id)
    db.commit()
    db.refresh(cert)
    return cert


async def _fetch_logo_bytes(logo_url: str | None) -> bytes | None:
    if not logo_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(logo_url)
        return response.content if response.status_code == 200 else None
    except Exception:
        return None


async def render_certificate_pdf(certificate: Certificate, student_name: str, organization: Organization) -> bytes:
    from reportlab.lib.colors import HexColor, black
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    width, height = landscape(letter)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(letter))

    accent = HexColor(organization.primary_color) if organization.primary_color else HexColor("#0f6b5c")

    pdf.setStrokeColor(accent)
    pdf.setLineWidth(3)
    pdf.rect(24, 24, width - 48, height - 48)
    pdf.setLineWidth(1)
    pdf.rect(32, 32, width - 64, height - 64)

    logo_bytes = await _fetch_logo_bytes(organization.logo_url)
    if logo_bytes:
        try:
            image = ImageReader(BytesIO(logo_bytes))
            pdf.drawImage(image, width / 2 - 30, height - 120, width=60, height=60, mask="auto", preserveAspectRatio=True)
        except Exception:
            pass

    pdf.setFillColor(accent)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 140, organization.name.upper())

    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 30)
    cert_kind = {
        "surah_completion": "Completion",
        "juz_completion": "Completion",
        "attendance": "Attendance",
        "competition": "Achievement",
    }.get(certificate.type, "Achievement")
    pdf.drawCentredString(width / 2, height - 190, "Certificate of " + cert_kind)

    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 225, "This certificate is proudly presented to")

    pdf.setFont("Helvetica-Bold", 26)
    pdf.setFillColor(accent)
    pdf.drawCentredString(width / 2, height - 265, student_name)

    pdf.setFillColor(black)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(width / 2, height - 300, certificate.title.replace("\u2014", "-"))

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 325, certificate.detail)

    issue_date = certificate.issued_at.strftime("%B %-d, %Y") if hasattr(certificate.issued_at, "strftime") else str(certificate.issued_at)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, height - 350, f"Issued {issue_date}")

    signer_name = certificate.issued_by_teacher.user.name if certificate.issued_by_teacher else organization.name
    pdf.setFont("Helvetica-Oblique", 14)
    pdf.drawCentredString(width / 2, 90, signer_name)
    pdf.setLineWidth(0.5)
    pdf.line(width / 2 - 100, 82, width / 2 + 100, 82)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 68, "Teacher" if certificate.issued_by_teacher else "Issued automatically")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
