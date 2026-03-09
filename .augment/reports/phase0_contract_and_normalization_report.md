# Phase 0 Contract and Normalization Report

## Introduction

This report records the Phase 0 implementation completed from the planning documents in `.augment/`.

Assumption:
- The request said to place the report at `.augment/report`.
- The repository already uses `.augment/reports/` for implementation reports.
- I used `.augment/reports/` as the safest repo-consistent location.

## Scope Completed

Phase 0 was kept contract-first and local-first.

Implemented:
- frozen runtime contracts for `document_manifest`, `pieces_index`, `branch_a_render`, `branch_c_render`, `clusters_render`, and `audio_manifest`
- sample normalization helpers grounded in the current `data/` layout
- document identity and variant rules
- deterministic rendered artifact path conventions under `sample_data/rendered/<document_id>/`
- stable interface seams for artifact store, document repository, preferences repository, and auth verification
- a minimal shell app scaffold required to hold the Phase 0 foundation

Not implemented:
- importer/packager execution logic
- Branch A reader behavior
- Branch C navigation behavior
- Branch B overlay behavior
- auth, upload, sync, cloud storage, or production infrastructure wiring

## Main Decisions Frozen in Phase 0

- **Canonical pieces remain the shared source of truth.**
- **`document_id`** uses the renderer-facing form `<family_id>-<variant_id>`, for example `sample01-a`.
- **`source_bundle_id`** uses the raw-pipeline-facing form `<family_id>_p03_bundle_<variant_id>`, for example `sample01_p03_bundle_a`.
- Imported sample normalization paths use `sample_data/imported/<family_id>/<variant_id>/`.
- Rendered contract paths use `sample_data/rendered/<document_id>/<artifact>.json`.
- Raw Markdown and unstable raw pipeline artifacts are not promoted to runtime contracts.

## Files Created or Changed

- `requirements.txt`
- `Procfile`
- `main.py`
- `.augment/config/placeholders.env`
- `app/__init__.py`
- `app/errors.py`
- `app/settings.py`
- `app/dependencies.py`
- `app/main.py`
- `app/routes/__init__.py`
- `app/routes/health.py`
- `app/routes/ui_shell.py`
- `app/templates/base.html`
- `app/templates/pages/home.html`
- `app/static/css/app.css`
- `app/static/js/app.js`
- `app/core/__init__.py`
- `app/core/ids.py`
- `app/core/render_artifacts.py`
- `app/core/sample_normalization.py`
- `app/core/interfaces/*`
- `app/core/contracts/*`
- `tests/contracts/test_contracts.py`
- `tests/contracts/test_sample_normalization.py`
- `tests/routes/test_phase0_smoke.py`

## Validation Run

Commands run:
- `python3 -m unittest discover -s tests/contracts -v`
- `python3 -m unittest discover -s tests/routes -v`
- `python3 -m compileall app tests main.py`

Results:
- 14 contract and normalization tests passed
- 1 route smoke test was skipped because `fastapi` and `httpx` are not installed locally
- syntax compilation passed

## Issues Found and Corrected During Validation

- The first implementation used **Pydantic v2** validators, but the local environment has **Pydantic 1.10.14**.
- Contracts were updated to Pydantic v1-compatible validators and frozen-model configuration.
- A naming mismatch was corrected so that `source_bundle_id` consistently uses underscores, matching the planning documents and `data/` artifacts.

## Remaining Ambiguities

- `DocumentManifest.title` is currently defined, but the exact title derivation rule is still a later packager concern.
- The app scaffold exists, but full app validation requires installing the planned FastAPI test/runtime dependencies.
- Phase 1 should begin with the renderer packaging/import layer, not direct UI feature expansion.

## Recommended Next Step

Before Phase 1:
- approve this Phase 0 baseline
- optionally approve dependency installation so FastAPI routes can be validated without skips
- then begin the renderer packaging layer that emits the frozen contracts defined here