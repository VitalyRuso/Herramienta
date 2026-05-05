from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import create_db_and_tables
from app.routes import export, leads, pages, analysis

app = FastAPI(
    title="Scraping",
    description="Herramienta para detectar, enriquecer y exportar leads B2B.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    """Inicializa la base de datos y limpia exportaciones antiguas."""
    create_db_and_tables()
    cleanup_old_exports()


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(leads.router)
app.include_router(analysis.router)
app.include_router(export.router)


@app.get("/health")
def health() -> dict:
    """Comprueba que la aplicación funciona."""
    return {
        "status": "ok",
        "service": "scraping"
    }

from app.services.exporters import cleanup_old_exports