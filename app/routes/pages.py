from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["Páginas"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Página principal de la herramienta."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )