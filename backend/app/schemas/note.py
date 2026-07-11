from datetime import datetime

from app.schemas.base import CamelModel


class NoteOut(CamelModel):
    id: str
    content: str
    surah_number: int | None
    ayah_number: int | None
    created_at: datetime


class NoteCreate(CamelModel):
    content: str
    surah_number: int | None = None
    ayah_number: int | None = None
    client_mutation_id: str | None = None
