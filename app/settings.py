"""Local-first application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    log_level: str
    artifact_store_backend: str
    document_repo_backend: str
    preferences_repo_backend: str
    auth_backend: str
    project_root: Path
    raw_artifacts_root: Path
    sample_data_root: Path
    sample_import_root: Path
    render_output_root: Path
    templates_dir: Path
    static_dir: Path


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    sample_data_root = Path(
        os.getenv("APP_SAMPLE_DATA_ROOT", project_root / "sample_data")
    ).resolve()
    return Settings(
        app_name=os.getenv("APP_APP_NAME", "Transcript Renderer"),
        app_env=os.getenv("APP_APP_ENV", "dev"),
        log_level=os.getenv("APP_LOG_LEVEL", "INFO"),
        artifact_store_backend=os.getenv("APP_ARTIFACT_STORE_BACKEND", "localfs"),
        document_repo_backend=os.getenv("APP_DOCUMENT_REPO_BACKEND", "localfs"),
        preferences_repo_backend=os.getenv("APP_PREFERENCES_REPO_BACKEND", "memory"),
        auth_backend=os.getenv("APP_AUTH_BACKEND", "fake"),
        project_root=project_root,
        raw_artifacts_root=Path(
            os.getenv("APP_RAW_ARTIFACTS_ROOT", project_root / "data")
        ).resolve(),
        sample_data_root=sample_data_root,
        sample_import_root=(sample_data_root / "imported").resolve(),
        render_output_root=Path(
            os.getenv("APP_RENDER_OUTPUT_ROOT", sample_data_root / "rendered")
        ).resolve(),
        templates_dir=(project_root / "app" / "templates").resolve(),
        static_dir=(project_root / "app" / "static").resolve(),
    )


settings = load_settings()