import csv
import io
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Lead
from app.schemas import UrlAnalysisRequest
from app.services.enrichment import enrich_lead
from app.services.url_analyzer import analyze_url

router = APIRouter(prefix="/api", tags=["Análisis"])


def schema_to_dict(data):
    """Convierte un schema Pydantic/SQLModel a diccionario compatible."""
    if hasattr(data, "model_dump"):
        return data.model_dump()
    return data.dict()


def normalize_url_for_compare(url: str | None) -> str | None:
    """Normaliza una URL para comparar y evitar duplicados."""
    if not url:
        return None

    clean_url = url.strip().lower()

    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    parsed = urlparse(clean_url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")

    return f"{domain}{path}"


def find_existing_lead(session: Session, website: str | None, source_url: str | None) -> Lead | None:
    """Busca un lead existente para evitar duplicados."""
    target_website = normalize_url_for_compare(website)
    target_source = normalize_url_for_compare(source_url)

    leads = session.exec(select(Lead)).all()

    for lead in leads:
        lead_website = normalize_url_for_compare(lead.website)
        lead_source = normalize_url_for_compare(lead.source_url)

        if target_website and lead_website == target_website:
            return lead

        if target_source and lead_source == target_source:
            return lead

    return None


def save_detected_lead(
    session: Session,
    lead_data,
    sector: str,
    city: str,
    country: str,
) -> Lead:
    """Guarda o actualiza un lead detectado desde URL."""
    existing_lead = find_existing_lead(
        session=session,
        website=lead_data.website,
        source_url=lead_data.source_url,
    )

    if existing_lead:
        existing_lead.sector = sector
        existing_lead.city = city
        existing_lead.country = country
        existing_lead.website = lead_data.website or existing_lead.website
        existing_lead.phone = lead_data.phone or existing_lead.phone
        existing_lead.generic_email = lead_data.generic_email or existing_lead.generic_email
        existing_lead.social_links = lead_data.social_links or existing_lead.social_links
        existing_lead.source_url = lead_data.source_url or existing_lead.source_url
        existing_lead.source_type = lead_data.source_type or existing_lead.source_type

        lead = enrich_lead(existing_lead)
    else:
        lead = Lead(**schema_to_dict(lead_data))
        lead = enrich_lead(lead)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    return lead


def looks_like_url(value: str) -> bool:
    """Comprueba si un texto parece una URL o dominio."""
    value = value.strip()

    if not value:
        return False

    if "@" in value:
        return False

    if value.startswith(("http://", "https://", "www.")):
        return True

    if "." in value and " " not in value:
        parts = value.split(".")
        return len(parts[-1]) >= 2

    return False


def extract_urls_from_text(text: str) -> list[str]:
    """Extrae URLs desde texto plano o CSV simple."""
    urls = []

    # Primero intentamos leerlo como CSV.
    reader = csv.reader(io.StringIO(text))

    for row in reader:
        for cell in row:
            clean_cell = cell.strip()

            if looks_like_url(clean_cell) and clean_cell not in urls:
                urls.append(clean_cell)

    # También revisamos línea por línea por si es TXT.
    for line in text.splitlines():
        clean_line = line.strip()

        if looks_like_url(clean_line) and clean_line not in urls:
            urls.append(clean_line)

    return urls


MAX_URLS_PER_ANALYSIS = 100

@router.post("/analyze-urls")
def analyze_urls(
    data: UrlAnalysisRequest,
    session: Session = Depends(get_session)
) -> dict:
    """Analiza URLs públicas y guarda empresas detectadas."""
    
    # Limpiar URLs vacías y contar reales
    urls = [url.strip() for url in data.urls if url.strip()]
    
    if len(urls) > MAX_URLS_PER_ANALYSIS:
        raise HTTPException(
            status_code=400,
            detail=f"El límite máximo es de {MAX_URLS_PER_ANALYSIS} URLs por análisis."
        )

    created_leads = []
    errors = []

    for clean_url in urls:
        try:
            lead_data = analyze_url(
                url=clean_url,
                sector=data.sector,
                city=data.city,
                country=data.country,
            )

            lead = save_detected_lead(
                session=session,
                lead_data=lead_data,
                sector=data.sector,
                city=data.city,
                country=data.country,
            )

            created_leads.append(lead)

        except Exception as error:
            errors.append({
                "url": clean_url,
                "error": str(error)
            })

    return {
        "status": "ok",
        "created": len(created_leads),
        "errors": errors,
        "leads": created_leads,
    }


@router.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    sector: str = Form(...),
    city: str = Form(...),
    country: str = Form("España"),
    session: Session = Depends(get_session),
) -> dict:
    """Analiza URLs cargadas desde un archivo TXT o CSV."""
    content = await file.read()

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    urls = extract_urls_from_text(text)

    created_leads = []
    errors = []

    for url in urls:
        try:
            lead_data = analyze_url(
                url=url,
                sector=sector,
                city=city,
                country=country,
            )

            lead = save_detected_lead(
                session=session,
                lead_data=lead_data,
                sector=sector,
                city=city,
                country=country,
            )

            created_leads.append(lead)

        except Exception as error:
            errors.append({
                "url": url,
                "error": str(error)
            })

    return {
        "status": "ok",
        "filename": file.filename,
        "total_urls_detected": len(urls),
        "created": len(created_leads),
        "errors": errors,
        "leads": created_leads,
    }


@router.get("/stats")
def get_stats(session: Session = Depends(get_session)) -> dict:
    """Devuelve estadísticas básicas de leads."""
    leads = session.exec(select(Lead)).all()

    total = len(leads)
    avg_score = round(sum(lead.lead_score for lead in leads) / total, 2) if total else 0

    cities = {}
    sectors = {}

    for lead in leads:
        cities[lead.city] = cities.get(lead.city, 0) + 1
        sectors[lead.sector] = sectors.get(lead.sector, 0) + 1

    return {
        "total_leads": total,
        "average_score": avg_score,
        "cities": cities,
        "sectors": sectors,
    }