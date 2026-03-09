"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.dependencies import get_settings
from app.routes.health import router as health_router
from app.routes.ui_shell import router as shell_router


def build_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(shell_router)
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    return app


app = build_app()