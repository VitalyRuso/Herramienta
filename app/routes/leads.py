from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func
from sqlmodel import Session, select

from app.database import get_session
from app.models import Lead
from app.schemas import LeadCreate
from app.services.enrichment import enrich_lead
from app.services.scoring import calculate_lead_score

router = APIRouter(prefix="/api/leads", tags=["Leads"])


def schema_to_dict(data):
    """Convierte un schema Pydantic/SQLModel a diccionario de forma compatible."""
    if hasattr(data, "model_dump"):
        return data.model_dump()
    return data.dict()


@router.post("")
def create_lead(data: LeadCreate, session: Session = Depends(get_session)) -> Lead:
    """Crea un lead manualmente."""
    lead = Lead(**schema_to_dict(data))
    lead.lead_score = calculate_lead_score(lead)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    return lead


@router.get("")
def list_leads(
    sector: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    min_score: int = Query(default=0),
    session: Session = Depends(get_session)
) -> list[Lead]:
    """Lista leads usando filtros directamente en la base de datos."""
    query = select(Lead)

    if sector:
        query = query.where(func.lower(Lead.sector).contains(sector.lower()))

    if city:
        query = query.where(func.lower(Lead.city).contains(city.lower()))

    query = query.where(Lead.lead_score >= min_score)
    query = query.order_by(Lead.lead_score.desc())

    leads = session.exec(query).all()
    return leads


@router.get("/{lead_id}")
def get_lead(lead_id: int, session: Session = Depends(get_session)) -> Lead:
    """Obtiene un lead por id."""
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    return lead


@router.post("/{lead_id}/enrich")
def enrich_existing_lead(
    lead_id: int,
    session: Session = Depends(get_session)
) -> Lead:
    """Enriquece un lead existente y recalcula su puntuación."""
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    lead = enrich_lead(lead)

    session.add(lead)
    session.commit()
    session.refresh(lead)

    return lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, session: Session = Depends(get_session)) -> dict:
    """Elimina un lead concreto."""
    lead = session.get(Lead, lead_id)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    session.delete(lead)
    session.commit()

    return {
        "status": "ok",
        "message": "Lead eliminado correctamente",
        "lead_id": lead_id
    }


@router.delete("")
def delete_all_leads(session: Session = Depends(get_session)) -> dict:
    """Elimina todos los leads guardados."""
    leads = session.exec(select(Lead)).all()

    total = len(leads)

    for lead in leads:
        session.delete(lead)

    session.commit()

    return {
        "status": "ok",
        "message": "Todos los leads han sido eliminados",
        "total_deleted": total
    }