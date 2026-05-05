from typing import Optional

from sqlmodel import SQLModel


class LeadCreate(SQLModel):
    """Datos necesarios para crear un lead."""

    company_name: str
    sector: str
    city: str
    country: str = "España"
    website: Optional[str] = None
    phone: Optional[str] = None
    generic_email: Optional[str] = None
    social_links: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "manual"
    notes: Optional[str] = None


class UrlAnalysisRequest(SQLModel):
    """Petición para analizar varias URLs públicas."""

    urls: list[str]
    sector: str = "sin especificar"
    city: str = "sin especificar"
    country: str = "España"