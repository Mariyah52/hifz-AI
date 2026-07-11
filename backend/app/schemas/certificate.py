from datetime import datetime
from typing import Literal

from app.schemas.base import CamelModel

CertificateType = Literal["surah_completion", "juz_completion", "attendance", "competition"]


class CertificateOut(CamelModel):
    id: str
    type: CertificateType
    title: str
    detail: str
    issued_by_teacher_name: str | None
    issued_at: datetime


class IssueCertificateRequest(CamelModel):
    type: Literal["attendance", "competition"]
    title: str
    detail: str
