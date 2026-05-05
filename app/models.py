from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Lead(SQLModel, table=True):
    """Modelo principal para guardar empresas detectadas."""

    id: Optional[int] = Field(default=None, primary_key=True)

    company_name: str
    sector: str
    city: str
    country: str = "España"

    website: Optional[str] = None
    phone: Optional[str] = None
    generic_email: Optional[str] = None
    social_links: Optional[str] = None

    source_url: Optional[str] = None
    source_type: str = "demo"

    lead_score: int = 0
    opportunity_score: int = 0
    opportunity_tags: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)