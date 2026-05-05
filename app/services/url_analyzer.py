import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.schemas import LeadCreate


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

PHONE_REGEX = re.compile(
    r"(\+34[\s.-]?)?(\d[\s.-]?){9,}"
)

GENERIC_EMAIL_PREFIXES = (
    "info",
    "contacto",
    "contact",
    "hola",
    "ventas",
    "comercial",
    "soporte",
    "support",
    "hello",
    "booking",
    "reservas",
    "administracion",
    "administración",
)

EMAILS_NO_COMERCIALES = (
    "webmaster",
    "admin",
    "noreply",
    "no-reply",
    "privacy",
    "legal",
    "abuse",
    "postmaster",
)

SOCIAL_DOMAINS = (
    "instagram.com",
    "facebook.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
)

CONTACT_PATHS = (
    "/contacto",
    "/contact",
    "/contactanos",
    "/contáctanos",
    "/sobre-nosotros",
    "/sobre-nosotras",
    "/quienes-somos",
    "/quiénes-somos",
    "/about",
    "/about-us",
)


def normalize_url(url: str) -> str:
    """Normaliza una URL añadiendo https si falta."""
    clean_url = url.strip()

    if not clean_url:
        return ""

    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    return clean_url


def get_base_url(url: str) -> str:
    """Devuelve la URL base de un dominio."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_html(url: str) -> tuple[str, str]:
    """Descarga HTML de una URL pública con timeout razonable."""
    headers = {
        "User-Agent": (
            "WebTerritorioMasterLeadFinder/0.1 "
            "(herramienta de análisis B2B; uso razonable)"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=5,
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise ValueError(f"La URL no parece HTML: {content_type}")

    return response.text, response.url


def extract_company_name(soup: BeautifulSoup, url: str) -> str:
    """Intenta detectar el nombre de empresa desde metadatos, title o dominio."""
    og_site_name = soup.find("meta", property="og:site_name")

    if og_site_name and og_site_name.get("content"):
        return og_site_name["content"].strip()

    application_name = soup.find("meta", attrs={"name": "application-name"})

    if application_name and application_name.get("content"):
        return application_name["content"].strip()

    title = soup.find("title")

    if title and title.text:
        title_text = title.text.strip()
        return title_text.split("|")[0].split("-")[0].strip()[:120]

    domain = urlparse(url).netloc.replace("www.", "")
    return domain.split(".")[0].replace("-", " ").title()


def extract_emails(text: str) -> list[str]:
    """Extrae emails únicos desde texto visible o HTML."""
    emails = EMAIL_REGEX.findall(text)
    unique_emails = []

    for email in emails:
        clean_email = email.strip().lower()

        if clean_email not in unique_emails:
            unique_emails.append(clean_email)

    return unique_emails


def choose_generic_email(emails: list[str]) -> str | None:
    """Elige un email útil para contacto comercial B2B."""
    emails_limpios = []

    for email in emails:
        prefix = email.split("@")[0].lower()

        if prefix in EMAILS_NO_COMERCIALES:
            continue

        emails_limpios.append(email)

    for email in emails_limpios:
        prefix = email.split("@")[0].lower()

        if prefix in GENERIC_EMAIL_PREFIXES:
            return email

    # Si no hay email claramente comercial, no forzamos uno malo.
    return None

def extract_phone(text: str) -> str | None:
    """Extrae un teléfono español razonable si aparece en la página."""
    matches = PHONE_REGEX.finditer(text)

    for match in matches:
        candidate = normalize_spanish_phone(match.group(0))

        if candidate:
            return candidate

    return None


def extract_social_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extrae enlaces de redes sociales públicas."""
    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        absolute_url = urljoin(base_url, href)

        if any(domain in absolute_url.lower() for domain in SOCIAL_DOMAINS):
            if absolute_url not in links:
                links.append(absolute_url)

    return links[:5]


def extract_mailto_emails(soup: BeautifulSoup) -> list[str]:
    """Extrae emails desde enlaces mailto."""
    emails = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if href.lower().startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip().lower()

            if email and email not in emails:
                emails.append(email)

    return emails


def extract_tel_phone(soup: BeautifulSoup) -> str | None:
    """Extrae teléfono desde enlaces tel."""
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if href.lower().startswith("tel:"):
            candidate = normalize_spanish_phone(href.replace("tel:", ""))

            if candidate:
                return candidate

    return None

def normalize_spanish_phone(raw_phone: str) -> str | None:
    """Normaliza y valida teléfonos españoles reales.

    Solo acepta números españoles de 9 cifras que empiezan por 6, 7, 8 o 9.
    Evita capturar números largos aleatorios de una web.
    """
    phone = re.sub(r"[^\d+]", "", raw_phone)

    if phone.startswith("+34"):
        digits = re.sub(r"\D", "", phone.replace("+34", ""))

        if len(digits) == 9 and digits[0] in ("6", "7", "8", "9"):
            return "+34" + digits

        return None

    digits_only = re.sub(r"\D", "", phone)

    if len(digits_only) == 9 and digits_only[0] in ("6", "7", "8", "9"):
        return "+34" + digits_only

    return None

def collect_pages(url: str) -> list[tuple[str, BeautifulSoup, str]]:
    """Recoge la página principal y algunas páginas típicas de contacto."""
    normalized_url = normalize_url(url)
    base_url = get_base_url(normalized_url)

    pages = []

    html, final_url = fetch_html(normalized_url)
    pages.append((final_url, BeautifulSoup(html, "html.parser"), html))

    for path in CONTACT_PATHS:
        candidate_url = urljoin(base_url, path)

        try:
            html, final_url = fetch_html(candidate_url)
            pages.append((final_url, BeautifulSoup(html, "html.parser"), html))
        except Exception:
            # Si una ruta típica no existe, simplemente se ignora.
            continue

    return pages


def analyze_url(
    url: str,
    sector: str = "sin especificar",
    city: str = "sin especificar",
    country: str = "España",
) -> LeadCreate:
    """Analiza una URL pública y devuelve un lead detectado."""
    normalized_url = normalize_url(url)

    if not normalized_url:
        raise ValueError("URL vacía")

    pages = collect_pages(normalized_url)

    first_url, first_soup, first_html = pages[0]
    base_url = get_base_url(first_url)

    company_name = extract_company_name(first_soup, first_url)

    all_emails = []
    all_social_links = []
    phone = None

    analyzed_pages = []

    for page_url, soup, html in pages:
        analyzed_pages.append(page_url)

        page_text = soup.get_text(" ", strip=True)
        combined_text = f"{page_text} {html}"

        all_emails.extend(extract_emails(combined_text))
        all_emails.extend(extract_mailto_emails(soup))

        if not phone:
            phone = extract_tel_phone(soup) or extract_phone(combined_text)

        social_links = extract_social_links(soup, base_url)

        for social_link in social_links:
            if social_link not in all_social_links:
                all_social_links.append(social_link)

    unique_emails = []

    for email in all_emails:
        if email not in unique_emails:
            unique_emails.append(email)

    generic_email = choose_generic_email(unique_emails)
    social_links_text = ", ".join(all_social_links[:5]) if all_social_links else None

    notes = []

    if generic_email:
        notes.append("Email genérico detectado.")

    if phone:
        notes.append("Teléfono público detectado.")

    if social_links_text:
        notes.append("Redes sociales detectadas.")

    if len(pages) > 1:
        notes.append(f"Se revisaron {len(pages)} páginas del sitio.")

    if not generic_email and not phone:
        notes.append("Datos de contacto limitados. Revisar manualmente.")

    return LeadCreate(
        company_name=company_name or "Empresa detectada",
        sector=sector,
        city=city,
        country=country,
        website=base_url,
        phone=phone,
        generic_email=generic_email,
        social_links=social_links_text,
        source_url=normalized_url,
        source_type="url_analysis",
        notes=" ".join(notes) or "Lead detectado desde URL pública.",
    )