"""Phase 0 shell routes."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.dependencies import get_settings

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory=str(get_settings().templates_dir))


@router.get("/ui")
def ui_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={"page_title": "Transcript Renderer"},
    )