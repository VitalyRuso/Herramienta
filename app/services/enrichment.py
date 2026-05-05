from datetime import datetime

from app.models import Lead
from app.services.opportunity import analyze_opportunity
from app.services.scoring import calculate_lead_score


def enrich_lead(lead: Lead) -> Lead:
    """Enriquece un lead con reglas simples para el MVP."""
    notes = []

    if lead.website:
        notes.append("Tiene web. Revisar calidad visual, SEO y velocidad.")
    else:
        notes.append("No tiene web detectada. Posible oportunidad para crear página web.")

    if lead.generic_email:
        notes.append("Tiene email genérico de empresa.")
    else:
        notes.append("No tiene email genérico detectado.")

    if lead.phone:
        notes.append("Tiene teléfono público.")
    else:
        notes.append("No tiene teléfono detectado.")

    if lead.social_links:
        notes.append("Tiene redes sociales públicas.")
    else:
        notes.append("No tiene redes sociales detectadas.")

    lead.notes = " ".join(notes)
    lead.lead_score = calculate_lead_score(lead)
    lead = analyze_opportunity(lead)
    lead.updated_at = datetime.utcnow()

    return lead