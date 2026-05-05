from app.models import Lead


SECTORES_CON_BUENA_OPORTUNIDAD = {
    "restaurantes",
    "reformas",
    "clinicas",
    "clínicas",
    "talleres",
    "inmobiliarias",
    "dentistas",
    "peluquerias",
    "peluquerías",
    "autoescuelas",
    "gimnasios",
    "abogados",
}


def analyze_opportunity(lead: Lead) -> Lead:
    """Analiza la oportunidad comercial de un lead.

    La lógica no mide solo si el lead está completo.
    También mide si puede necesitar servicios digitales, web, marketing o mejora comercial.
    """
    opportunity_score = 0
    tags = []

    if not lead.website:
        opportunity_score += 30
        tags.append("sin_web")
    else:
        opportunity_score += 10
        tags.append("tiene_web")

    if not lead.generic_email:
        opportunity_score += 20
        tags.append("sin_email_visible")
    else:
        tags.append("email_visible")

    if not lead.phone:
        opportunity_score += 15
        tags.append("sin_telefono_visible")
    else:
        tags.append("telefono_visible")

    if not lead.social_links:
        opportunity_score += 15
        tags.append("sin_redes_detectadas")
    else:
        tags.append("redes_detectadas")

    sector = (lead.sector or "").lower().strip()

    if sector in SECTORES_CON_BUENA_OPORTUNIDAD:
        opportunity_score += 15
        tags.append("sector_interesante")

    if lead.website and not lead.generic_email:
        opportunity_score += 10
        tags.append("contacto_debil")

    if lead.website and not lead.social_links:
        opportunity_score += 10
        tags.append("presencia_digital_mejorable")

    lead.opportunity_score = min(opportunity_score, 100)
    lead.opportunity_tags = ", ".join(tags)

    return lead


def get_opportunity_label(score: int) -> str:
    """Devuelve una etiqueta textual según la oportunidad."""
    if score >= 70:
        return "Alta"

    if score >= 40:
        return "Media"

    return "Baja"