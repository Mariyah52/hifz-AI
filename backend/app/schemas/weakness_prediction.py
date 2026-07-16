from app.schemas.base import CamelModel


class WeaknessPredictionOut(CamelModel):
    sabaq_id: str
    surah_number: int
    from_ayah: int
    to_ayah: int
    days_since_last_review: int
    days_until_due: int
    forgetting_risk_percent: float
    ease_factor: float
    basis: str
