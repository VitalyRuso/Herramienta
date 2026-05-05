import csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.models import Lead

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

def cleanup_old_exports(max_age_hours: int = 24) -> None:
    """Elimina archivos de exportación antiguos para mantener limpia la carpeta exports."""
    if not EXPORTS_DIR.exists():
        return

    now = datetime.now()
    max_age = timedelta(hours=max_age_hours)

    for file_path in EXPORTS_DIR.iterdir():
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in {".csv", ".xlsx"}:
            continue

        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)

        if now - modified_at > max_age:
            try:
                file_path.unlink()
            except OSError:
                # Si el archivo está en uso o no se puede borrar, lo ignoramos.
                continue

TAG_LABELS = {
    "sin_web": "Sin web detectada",
    "tiene_web": "Tiene web",
    "sin_email_visible": "Sin email visible",
    "email_visible": "Email visible",
    "sin_telefono_visible": "Sin teléfono visible",
    "telefono_visible": "Teléfono visible",
    "sin_redes_detectadas": "Sin redes detectadas",
    "redes_detectadas": "Redes detectadas",
    "sector_interesante": "Sector interesante",
    "contacto_debil": "Contacto débil",
    "presencia_digital_mejorable": "Presencia digital mejorable",
}


def get_value(lead: Lead, field: str, default: Any = None) -> Any:
    """Obtiene un valor del lead de forma segura."""
    return getattr(lead, field, default)


def get_lead_quality(score: int | None) -> str:
    """Devuelve la calidad del lead según su puntuación general."""
    score = score or 0

    if score >= 80:
        return "Alta"

    if score >= 50:
        return "Media"

    return "Baja"


def get_opportunity_label(score: int | None) -> str:
    """Devuelve la etiqueta de oportunidad comercial."""
    score = score or 0

    if score >= 70:
        return "Alta"

    if score >= 40:
        return "Media"

    return "Baja"

def get_priority_label(lead: Lead) -> str:
    """Calcula la prioridad comercial del lead para trabajar en Excel."""
    opportunity_score = get_value(lead, "opportunity_score", 0) or 0
    lead_score = lead.lead_score or 0

    if opportunity_score >= 70 or lead_score >= 80:
        return "Alta"

    if opportunity_score >= 40 or lead_score >= 50:
        return "Media"

    return "Baja"


def get_next_action(lead: Lead) -> str:
    """Sugiere la próxima acción comercial para este lead."""
    if not lead.website:
        return "Revisar empresa y valorar creación de página web."

    if lead.website and not lead.generic_email and not lead.phone:
        return "Buscar contacto alternativo antes de contactar."

    if lead.website and not lead.generic_email:
        return "Revisar web y buscar email o formulario de contacto."

    if lead.website and not lead.social_links:
        return "Valorar propuesta de mejora de presencia digital."

    if lead.generic_email or lead.phone:
        return "Contactar y presentar propuesta comercial."

    return "Revisar manualmente antes de contactar."


def get_commercial_reason(lead: Lead) -> str:
    """Resume por qué el lead puede ser interesante comercialmente."""
    reasons = []

    if not lead.generic_email:
        reasons.append("sin email visible")

    if not lead.phone:
        reasons.append("sin teléfono visible")

    if not lead.social_links:
        reasons.append("sin redes detectadas")

    if not lead.website:
        reasons.append("sin web detectada")
    else:
        reasons.append("web detectada")

    if get_value(lead, "opportunity_score", 0) >= 70:
        reasons.append("oportunidad comercial alta")

    if lead.lead_score >= 70:
        reasons.append("buen nivel de datos")

    if not reasons:
        return "Lead útil para revisión comercial."

    return ", ".join(reasons).capitalize() + "."

def format_opportunity_tags(value: str | None) -> str:
    """Convierte etiquetas internas en texto legible para empresa."""
    if not value:
        return "-"

    tags = [
        tag.strip()
        for tag in str(value).split(",")
        if tag.strip()
    ]

    if not tags:
        return "-"

    return ", ".join(TAG_LABELS.get(tag, tag.replace("_", " ")) for tag in tags)


def lead_to_row(lead: Lead) -> dict:
    """Convierte un lead en un diccionario exportable."""
    return {
        "id": lead.id,
        "company_name": lead.company_name,
        "sector": lead.sector,
        "city": lead.city,
        "country": lead.country,
        "website": lead.website,
        "phone": lead.phone,
        "generic_email": lead.generic_email,
        "social_links": lead.social_links,
        "source_url": lead.source_url,
        "source_type": lead.source_type,
        "lead_score": lead.lead_score,
        "lead_quality": get_lead_quality(lead.lead_score),
        "opportunity_score": get_value(lead, "opportunity_score", 0),
        "opportunity_label": get_opportunity_label(get_value(lead, "opportunity_score", 0)),
        "priority": get_priority_label(lead),
        "next_action": get_next_action(lead),
        "commercial_reason": get_commercial_reason(lead),
        "opportunity_tags": format_opportunity_tags(get_value(lead, "opportunity_tags", None)),
        "notes": lead.notes,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


def export_leads_to_csv(leads: list[Lead]) -> Path:
    """Exporta leads a CSV y devuelve la ruta del archivo."""
    file_path = EXPORTS_DIR / "leads_export.csv"

    fieldnames = [
        "id",
        "company_name",
        "sector",
        "city",
        "country",
        "website",
        "phone",
        "generic_email",
        "social_links",
        "source_url",
        "source_type",
        "lead_score",
        "lead_quality",
        "opportunity_score",
        "opportunity_label",
        "priority",
        "next_action",
        "commercial_reason",
        "opportunity_tags",
        "notes",
        "created_at",
        "updated_at",
    ]

    with file_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for lead in leads:
            writer.writerow(lead_to_row(lead))

    return file_path


def apply_header_style(sheet, row_number: int = 1) -> None:
    """Aplica estilo profesional a una fila de cabecera."""
    fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
    font = Font(color="FFFFFF", bold=True)
    alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for cell in sheet[row_number]:
        cell.fill = fill
        cell.font = font
        cell.alignment = alignment


def apply_table_style(sheet) -> None:
    """Aplica bordes, alineación y altura a una hoja."""
    thin_border = Border(
        left=Side(style="thin", color="E5E7EB"),
        right=Side(style="thin", color="E5E7EB"),
        top=Side(style="thin", color="E5E7EB"),
        bottom=Side(style="thin", color="E5E7EB"),
    )

    for row in sheet.iter_rows():
        for cell in row:
            cell.border = thin_border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for row_number in range(1, sheet.max_row + 1):
        sheet.row_dimensions[row_number].height = 24


def set_column_widths(sheet, widths: dict[str, int]) -> None:
    """Configura anchuras de columnas."""
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width


def apply_score_style(cell, score: int | None) -> None:
    """Colorea una celda según score."""
    score = score or 0

    if score >= 80:
        cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        cell.font = Font(color="166534", bold=True)
    elif score >= 50:
        cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        cell.font = Font(color="92400E", bold=True)
    else:
        cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        cell.font = Font(color="991B1B", bold=True)


def apply_opportunity_style(cell, label: str) -> None:
    """Colorea una celda según oportunidad comercial."""
    label = (label or "").lower()

    if label == "alta":
        cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        cell.font = Font(color="166534", bold=True)
    elif label == "media":
        cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        cell.font = Font(color="92400E", bold=True)
    else:
        cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        cell.font = Font(color="991B1B", bold=True)


def add_hyperlink(cell, url: str | None) -> None:
    """Añade hipervínculo si la URL existe."""
    if not url:
        return

    cell.value = url
    cell.hyperlink = url
    cell.style = "Hyperlink"


def create_summary_sheet(workbook: Workbook, leads: list[Lead]) -> None:
    """Crea una hoja resumen con métricas principales."""
    sheet = workbook.active
    sheet.title = "Resumen"

    total = len(leads)
    average_score = round(sum((lead.lead_score or 0) for lead in leads) / total, 2) if total else 0
    average_opportunity = round(
        sum(get_value(lead, "opportunity_score", 0) for lead in leads) / total,
        2
    ) if total else 0

    high_opportunity = sum(
        1 for lead in leads
        if get_opportunity_label(get_value(lead, "opportunity_score", 0)) == "Alta"
    )

    with_email = sum(1 for lead in leads if lead.generic_email)
    with_phone = sum(1 for lead in leads if lead.phone)
    with_website = sum(1 for lead in leads if lead.website)

    city_counter = Counter(lead.city for lead in leads if lead.city)
    sector_counter = Counter(lead.sector for lead in leads if lead.sector)

    sheet.merge_cells("A1:H1")
    sheet.merge_cells("A2:H2")

    sheet["A2"] = "Resumen profesional de leads B2B"
    sheet["A4"] = "Fecha de exportación"
    sheet["A1"] = "Scraping"
    sheet["B4"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    sheet["A1"].font = Font(size=22, bold=True, color="111827")
    sheet["A1"].alignment = Alignment(horizontal="left", vertical="center")

    sheet["A2"].font = Font(size=12, color="6B7280")
    sheet["A2"].alignment = Alignment(horizontal="left", vertical="center")

    sheet["A4"].font = Font(bold=True, color="111827")
    sheet["B4"].font = Font(color="111827")

    sheet.row_dimensions[1].height = 32
    sheet.row_dimensions[2].height = 24

    sheet["A6"] = "Métrica"
    sheet["B6"] = "Valor"

    rows = [
        ("Total leads", total),
        ("Score medio", average_score),
        ("Oportunidad media", average_opportunity),
        ("Leads con oportunidad alta", high_opportunity),
        ("Leads con web", with_website),
        ("Leads con email", with_email),
        ("Leads con teléfono", with_phone),
        ("Ciudades detectadas", len(city_counter)),
        ("Sectores detectados", len(sector_counter)),
    ]

    for row in rows:
        sheet.append(row)

    sheet["D6"] = "Top ciudades"
    sheet["E6"] = "Leads"

    row_index = 7
    for city, count in city_counter.most_common(8):
        sheet[f"D{row_index}"] = city
        sheet[f"E{row_index}"] = count
        row_index += 1

    sheet["G6"] = "Top sectores"
    sheet["H6"] = "Leads"

    row_index = 7
    for sector, count in sector_counter.most_common(8):
        sheet[f"G{row_index}"] = sector
        sheet[f"H{row_index}"] = count
        row_index += 1

    sheet["A1"].font = Font(size=20, bold=True, color="111827")
    sheet["A2"].font = Font(size=12, color="6B7280")
    sheet["A4"].font = Font(bold=True)

    for cell_range in ("A6:B6", "D6:E6", "G6:H6"):
        for row in sheet[cell_range]:
            for cell in row:
                cell.fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")

    apply_table_style(sheet)

    set_column_widths(sheet, {
    "A": 34,
    "B": 18,
    "C": 4,
    "D": 28,
    "E": 14,
    "F": 4,
    "G": 28,
    "H": 14,
        })

def create_leads_sheet(workbook: Workbook, leads: list[Lead]) -> None:
    """Crea la hoja principal de leads."""
    sheet = workbook.create_sheet("Leads")

    headers = [
        "ID",
        "Empresa",
        "Sector",
        "Ciudad",
        "País",
        "Web",
        "Teléfono",
        "Email",
        "Redes",
        "Score",
        "Calidad",
        "Oportunidad Score",
        "Oportunidad",
        "Prioridad",
        "Próxima acción",
        "Motivo comercial",
        "Razones / Etiquetas",
        "Notas",
        "Fuente",
        "Tipo fuente",
        "Creado",
        "Actualizado",
        ]

    sheet.append(headers)
    apply_header_style(sheet)

    sorted_leads = sorted(
        leads,
        key=lambda lead: (
            get_value(lead, "opportunity_score", 0) or 0,
            lead.lead_score or 0,
        ),
        reverse=True,
    )

    for lead in sorted_leads:
        row = lead_to_row(lead)

        sheet.append([
        row["id"],
        row["company_name"],
        row["sector"],
        row["city"],
        row["country"],
        row["website"],
        row["phone"],
        row["generic_email"],
        row["social_links"],
        row["lead_score"],
        row["lead_quality"],
        row["opportunity_score"],
        row["opportunity_label"],
        row["priority"],
        row["next_action"],
        row["commercial_reason"],
        row["opportunity_tags"],
        row["notes"],
        row["source_url"],
        row["source_type"],
        str(row["created_at"]),
        str(row["updated_at"]),
])

    for row_number in range(2, sheet.max_row + 1):
        web_cell = sheet[f"F{row_number}"]
        source_cell = sheet[f"S{row_number}"]

        add_hyperlink(web_cell, web_cell.value)
        add_hyperlink(source_cell, source_cell.value)

        apply_score_style(sheet[f"J{row_number}"], sheet[f"J{row_number}"].value)
        apply_score_style(sheet[f"L{row_number}"], sheet[f"L{row_number}"].value)
        apply_opportunity_style(sheet[f"M{row_number}"], sheet[f"M{row_number}"].value)
        apply_opportunity_style(sheet[f"N{row_number}"], sheet[f"N{row_number}"].value)

    apply_table_style(sheet)

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    set_column_widths(sheet, {
       "A": 8,
        "B": 34,
        "C": 20,
        "D": 18,
        "E": 14,
        "F": 38,
        "G": 18,
        "H": 28,
        "I": 36,
        "J": 12,
        "K": 14,
        "L": 18,
        "M": 18,
        "N": 16,
        "O": 46,
        "P": 46,
        "Q": 42,
        "R": 70,
        "S": 38,
        "T": 18,
        "U": 22,
        "V": 22,
        })


def create_instructions_sheet(workbook: Workbook) -> None:
    """Crea una hoja con instrucciones para interpretar el archivo."""
    sheet = workbook.create_sheet("Instrucciones")

    rows = [
        ("Campo", "Explicación"),
        ("Score", "Mide la calidad general del lead según datos encontrados."),
        ("Calidad", "Alta, Media o Baja según el score general."),
        ("Oportunidad Score", "Mide si la empresa puede ser interesante comercialmente."),
        ("Oportunidad", "Alta, Media o Baja según posibilidad de venta o mejora digital."),
        ("Prioridad", "Indica qué leads conviene revisar primero."),
        ("Próxima acción", "Sugerencia práctica para trabajar el lead."),
        ("Motivo comercial", "Resumen de por qué el lead puede ser interesante."),
        ("Razones / Etiquetas", "Motivos detectados: sin email, sin redes, contacto débil, presencia mejorable, etc."),
        ("Notas", "Resumen automático del análisis comercial."),
        ("Fuente", "URL desde la que se detectó o analizó la empresa."),
        ("Recomendación", "Priorizar leads con oportunidad Alta y revisar manualmente antes de contactar."),
    ]

    for row in rows:
        sheet.append(row)

        apply_header_style(sheet)
    apply_table_style(sheet)

    set_column_widths(sheet, {
    "A": 26,
    "B": 120,
})

        # Ajuste visual para textos largos de instrucciones.
    for row_number in range(1, sheet.max_row + 1):
        sheet.row_dimensions[row_number].height = 28

    # Filas largas: nota legal y recomendación.
    for row_number in range(1, sheet.max_row + 1):
        sheet.row_dimensions[row_number].height = 28

    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
            vertical="top",
            wrap_text=True
            )

def export_leads_to_excel(leads: list[Lead]) -> Path:
    """Exporta leads a Excel con formato profesional para empresa."""
    file_path = EXPORTS_DIR / "leads_export_profesional.xlsx"

    workbook = Workbook()

    create_summary_sheet(workbook, leads)
    create_leads_sheet(workbook, leads)
    create_instructions_sheet(workbook)

    workbook.save(file_path)

    return file_path