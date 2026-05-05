from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Lead
from app.services.exporters import export_leads_to_csv, export_leads_to_excel

router = APIRouter(prefix="/api/export", tags=["Exportación"])


@router.get("/csv")
def export_csv(session: Session = Depends(get_session)):
    """Exporta todos los leads a CSV."""
    leads = session.exec(select(Lead)).all()
    file_path = export_leads_to_csv(leads)

    return FileResponse(
        path=file_path,
        filename="leads_export.csv",
        media_type="text/csv"
    )


@router.get("/excel")
def export_excel(session: Session = Depends(get_session)):
    """Exporta todos los leads a Excel."""
    leads = session.exec(select(Lead)).all()
    file_path = export_leads_to_excel(leads)

    return FileResponse(
        path=file_path,
        filename="leads_export.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )