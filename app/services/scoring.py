from app.models import Lead

SECTORES_INTERESANTES = {
    "restaurantes",
    "reformas",
    "clinicas",
    "clínicas",
    "talleres",
    "inmobiliarias",
    "peluquerias",
    "peluquerías",
    "dentistas",
    "abogados",
    "autoescuelas",
    "gimnasios",
}


def calculate_lead_score(lead: Lead) -> int:
    """Calcula una puntuación comercial de 0 a 100."""
    score = 0

    if lead.website:
        score += 20

    if lead.generic_email:
        score += 15

    if lead.phone:
        score += 10

    if lead.social_links:
        score += 10

    if lead.notes:
        score += 10

    sector = (lead.sector or "").lower().strip()
    if sector in SECTORES_INTERESANTES:
        score += 15

    # Oportunidad básica: tiene presencia digital, pero puede necesitar mejora.
    if lead.website and lead.generic_email:
        score += 20

    return min(score, 100)