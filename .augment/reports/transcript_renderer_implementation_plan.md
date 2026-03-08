# Transcript Renderer — Implementation Plan (Code-Only)

Version: 2026-03-06  
Primary target deployment: **Google Cloud Run**  
Secondary evaluated option: **Google Compute Engine e2-micro Always Free** (not selected as the primary target)  
Companion documents:
- `transcript_renderer_architecture_report.md`
- `transcript_renderer_infrastructure_enablement_guide.md`

---

## 0. Read this first

This document is the **developer implementation plan** for the application code only.

It is organized on **two axes at the same time**:

1. **Layered delivery phases**  
   Each phase must produce something visible, testable, and measurable.  
   Each phase includes:
   - objective
   - module scope
   - commands to run
   - visible result
   - validation criteria
   - expected failure modes

2. **Parallelizable module lanes**  
   Within each phase, modules are separated by explicit contracts so that multiple developers can work independently.  
   Integration is expected to be low-risk **if and only if the contracts are followed exactly**.

Everything related to:
- Google Cloud project setup
- IAM
- Cloud Run
- Firestore enablement
- Firebase Auth setup
- GCS bucket creation
- CI/CD
- budgets, secrets, regions, and service enablement

belongs in the companion document:

**`transcript_renderer_infrastructure_enablement_guide.md`**

This document intentionally focuses on:
- repo structure
- Python/FastAPI/Jinja2/HTMX implementation
- JSON contracts
- UI behaviors
- local validation
- application-level integration

---

## 1. Selected implementation target

### 1.1 Infrastructure decision that this code plan assumes

Google Compute Engine **does** have an Always Free path:
- 1 non-preemptible `e2-micro` VM per month
- only in `us-west1`, `us-central1`, `us-east1`
- 30 GB-months of standard persistent disk
- 1 GB/month outbound transfer

However, this code plan still targets **Cloud Run** as the primary path because:
- lower ops burden
- easier deploy/rollback
- easier split between web path and background packaging
- better alignment with the already recommended architecture
- cleaner Git-based deployment path
- safer path for a PoC where development speed matters more than squeezing every free CPU hour

The infrastructure guide includes an appendix on how to adapt this app to a VM if you deliberately choose to do so later.

### 1.2 Functional target

This plan delivers the web application that lets a user:

- browse their transcript library
- open a document
- view **Branch A** as the default reading experience
- hover a piece to:
  - highlight it
  - see timestamps
  - open/play audio from the piece start
- toggle cluster overlays from **Branch B**
- open **Branch C** summary view
- hover summary sentences to inspect cited pieces
- jump from summary → transcript → audio
- sign in with Google or email/password
- keep document access scoped to the current user

### 1.3 Explicit non-goals for this implementation pass

These are **not** required in this implementation pass:
- fully implementing the upstream processing pipeline
- automatic ingestion from Google Drive
- upload-and-process orchestration from the UI
- background execution of Whisper / SAT / embeddings / clustering jobs
- final funded production hardening

Those later addendums are allowed only as placeholders or extension points.

---

## 2. Delivery model

## 2.1 Layered phases

| Phase | Goal | Visible output | Primary validation |
|---|---|---|---|
| P0 | Boot app skeleton and app shell | App boots, shell page renders | `/healthz`, `/ui`, static CSS/JS load |
| P1 | Local document catalog and loader | Sidebar with sample documents | Document list renders from sample data |
| P2 | Render manifest packaging | Deterministic normalized manifests | CLI packager outputs JSON manifests |
| P3 | Branch A reader + audio overlay | Piece hover, tooltip, audio seek | Hover highlights exact piece; audio starts at piece timestamp |
| P4 | Branch B cluster overlay | Cluster toggles and cluster highlighting | Cluster hover/click affects relevant pieces |
| P5 | Branch C reader + cross-view navigation | Summary sentence citations and jumps | Summary → transcript jump works |
| P6 | User auth + ownership + preferences | Login, user-scoped docs, saved reader prefs | Auth flow works; prefs persist |
| P7 | Cloud-ready adapters + async extension points | Same app can run against GCS/Firestore | Local and cloud adapters both pass the contract tests |

## 2.2 Parallel module lanes

These module lanes are designed to be implemented in parallel after P0 contracts are frozen.

| Lane | Purpose | First meaningful phase |
|---|---|---|
| L1 `core-contracts` | Shared schemas, IDs, errors, service interfaces | P0 |
| L2 `catalog-and-storage` | Local/GCS artifact discovery and load | P1 |
| L3 `manifest-packager` | Normalize raw/sample artifacts into renderer manifests | P2 |
| L4 `reader-branch-a` | Branch A rendering, hover, tooltip, audio overlay | P3 |
| L5 `reader-clusters` | Branch B cluster color logic and overlay panel | P4 |
| L6 `reader-branch-c` | Summary rendering, sentence citations, cross-view jump | P5 |
| L7 `auth-and-prefs` | Firebase auth integration and preference persistence | P6 |
| L8 `cloud-adapters` | Firestore, GCS, Cloud Run-friendly adapters | P7 |

## 2.3 Phase dependency graph

```text
P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7

Parallelizable after P0:
  L2 can start once core contracts for storage and document identity are frozen
  L3 can start once manifest contracts are frozen
  L4 and L5 can work from sample manifests
  L6 can work from summary fixture manifests even before real Branch C exists
  L7 can start with fake auth, then switch to Firebase
  L8 can mirror L2 adapters after local contracts are stable
```

---

## 3. Target repository structure

Use this repo layout exactly unless there is a strong reason to deviate.

```text
transcript_renderer/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── settings.py
│   ├── dependencies.py
│   ├── logging_config.py
│   ├── errors.py
│   ├── routes/
│   │   ├── health.py
│   │   ├── ui_shell.py
│   │   ├── ui_documents.py
│   │   ├── ui_reader.py
│   │   ├── api_documents.py
│   │   ├── api_reader.py
│   │   ├── api_prefs.py
│   │   └── api_auth.py
│   ├── core/
│   │   ├── ids.py
│   │   ├── enums.py
│   │   ├── contracts/
│   │   │   ├── document_manifest.py
│   │   │   ├── pieces_index.py
│   │   │   ├── branch_a_render.py
│   │   │   ├── clusters_render.py
│   │   │   ├── branch_c_render.py
│   │   │   ├── reader_prefs.py
│   │   │   └── api_payloads.py
│   │   └── interfaces/
│   │       ├── artifact_store.py
│   │       ├── document_repository.py
│   │       ├── preferences_repository.py
│   │       └── auth_verifier.py
│   ├── adapters/
│   │   ├── localfs/
│   │   │   ├── artifact_store.py
│   │   │   ├── document_repository.py
│   │   │   └── sample_loader.py
│   │   ├── gcs/
│   │   │   └── artifact_store.py
│   │   ├── firestore/
│   │   │   ├── document_repository.py
│   │   │   └── preferences_repository.py
│   │   └── firebase/
│   │       └── auth_verifier.py
│   ├── services/
│   │   ├── document_catalog_service.py
│   │   ├── document_loader_service.py
│   │   ├── manifest_packager_service.py
│   │   ├── reader_service.py
│   │   ├── audio_service.py
│   │   ├── cluster_service.py
│   │   ├── crosslink_service.py
│   │   └── preference_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── shell.html
│   │   ├── partials/
│   │   │   ├── sidebar.html
│   │   │   ├── topbar.html
│   │   │   ├── document_header.html
│   │   │   ├── reader_branch_a.html
│   │   │   ├── reader_branch_c.html
│   │   │   ├── cluster_panel.html
│   │   │   ├── audio_overlay.html
│   │   │   ├── auth_panel.html
│   │   │   └── toast.html
│   │   └── pages/
│   │       ├── home.html
│   │       ├── document.html
│   │       └── login.html
│   ├── static/
│   │   ├── css/
│   │   │   ├── app.css
│   │   │   ├── reader.css
│   │   │   └── clusters.css
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   ├── reader.js
│   │   │   ├── audio_player.js
│   │   │   ├── clusters.js
│   │   │   └── auth.js
│   │   └── vendor/
│   │       └── htmx.min.js
│   └── tools/
│       ├── unpack_sample_data.py
│       ├── build_render_manifests.py
│       ├── seed_fixture_branch_c.py
│       └── smoke_test.py
├── tests/
│   ├── contract/
│   ├── services/
│   ├── routes/
│   └── e2e/
├── sample_data/
│   └── .gitkeep
├── requirements.txt
├── Procfile
├── main.py
├── README.md
└── Makefile
```

### 3.1 Why this structure

- `core/contracts`: frozen JSON/Pydantic contracts shared everywhere
- `core/interfaces`: stable adapter interfaces
- `adapters`: local/cloud implementations
- `services`: pure application logic
- `routes`: HTTP translation layer only
- `templates/static`: minimal UI
- `tools`: data preparation and validation scripts
- `tests/contract`: protect seam quality between modules

This is a **modular monolith**. That is intentional for the PoC.

---

## 4. Shared contracts (must be frozen before feature work)

This is the most important section in the whole implementation plan.

If these contracts drift casually, parallel work becomes fragile.

## 4.1 Identity rules

### 4.1.1 Document identity

```python
# app/core/ids.py
from pydantic import BaseModel, Field

class DocumentIdentity(BaseModel):
    tenant_id: str = Field(..., description="User or workspace owner")
    document_id: str = Field(..., description="Stable renderer document ID")
    source_bundle_id: str = Field(..., description="Canonical source bundle ID")
```

Rules:
- `document_id` is stable for the renderer
- `source_bundle_id` points back to the upstream artifact family
- `tenant_id` scopes access

### 4.1.2 Piece identity

Rules:
- `piece_id` must be globally unique **within a document**
- piece IDs are never re-used for a different text span
- every renderable view references piece IDs, not duplicated text semantics
- piece IDs remain the anchor for:
  - timestamps
  - audio seek
  - clusters
  - summary citations
  - cross-view jumps

## 4.2 Core render manifests

The UI must not infer cross-view traceability from markdown parsing at runtime.

The UI must consume normalized render manifests.

### 4.2.1 `document_manifest.json`

Purpose:
- document metadata
- available views
- storage paths
- sample/production source description
- user ownership metadata

Example:

```json
{
  "document_id": "sample01",
  "tenant_id": "local-dev",
  "title": "Sample 01",
  "default_view": "branch_a",
  "available_views": ["branch_a", "branch_c"],
  "has_clusters": true,
  "has_audio": true,
  "source_bundle_id": "sample01_p03_bundle_a",
  "artifacts": {
    "pieces_index": "rendered/sample01/pieces_index.json",
    "branch_a_render": "rendered/sample01/branch_a_render.json",
    "clusters_render": "rendered/sample01/clusters_render.json",
    "branch_c_render": "rendered/sample01/branch_c_render.json",
    "audio_manifest": "rendered/sample01/audio_manifest.json"
  }
}
```

### 4.2.2 `pieces_index.json`

Purpose:
- canonical piece index consumed by every view
- piece → timestamps
- piece → cluster ID
- piece → text hash
- piece → DOM anchor ID

Example:

```json
{
  "document_id": "sample01",
  "pieces": [
    {
      "piece_id": "p0001",
      "start_s": 12.34,
      "end_s": 19.20,
      "text": "Original canonical piece text.",
      "cluster_id": "c02",
      "dom_anchor": "piece-p0001"
    }
  ]
}
```

### 4.2.3 `branch_a_render.json`

Purpose:
- exact render plan for Branch A
- headers and paragraphs interleaved
- each paragraph block references exact piece runs in original order

Example:

```json
{
  "document_id": "sample01",
  "blocks": [
    {"type": "h1", "text": "Main Title", "anchor": "a-h1-001"},
    {
      "type": "paragraph",
      "anchor": "a-p-001",
      "piece_runs": [
        {"piece_id": "p0001", "text": "First piece text."},
        {"piece_id": "p0002", "text": "Second piece text."}
      ]
    }
  ]
}
```

### 4.2.4 `clusters_render.json`

Purpose:
- Branch B overlay state for the renderer
- cluster titles, default colors, piece membership, optional ordering

Example:

```json
{
  "document_id": "sample01",
  "clusters": [
    {
      "cluster_id": "c02",
      "title": "Phenomenology of perception",
      "color_token": "violet",
      "piece_ids": ["p0001", "p0008", "p0014"]
    }
  ]
}
```

### 4.2.5 `branch_c_render.json`

Purpose:
- summary blocks with sentence-level citations
- UI does not parse inline textual cite syntax
- every summary sentence is pre-linked to the exact cited pieces

Example:

```json
{
  "document_id": "sample01",
  "blocks": [
    {"type": "h1", "text": "Grounded Summary", "anchor": "c-h1-001"},
    {
      "type": "summary_sentence",
      "sentence_id": "s0001",
      "text": "The speaker distinguishes lived perception from formal abstraction.",
      "cited_piece_ids": ["p0003", "p0004", "p0005"],
      "dom_anchor": "summary-s0001"
    }
  ]
}
```

### 4.2.6 `audio_manifest.json`

Purpose:
- tell the renderer how to resolve audio playback

Example:

```json
{
  "document_id": "sample01",
  "audio_url": "/media/sample01/audio",
  "duration_s": 3812.24,
  "waveform_url": null
}
```

## 4.3 HTTP/API contracts

These endpoints are sufficient for the PoC.

### 4.3.1 UI routes

| Route | Method | Purpose |
|---|---|---|
| `/ui` | GET | shell/home |
| `/ui/documents/{document_id}` | GET | open default document page |
| `/ui/documents/{document_id}/branch-a` | GET | Branch A reader fragment/page |
| `/ui/documents/{document_id}/branch-c` | GET | Branch C reader fragment/page |
| `/ui/documents/{document_id}/clusters` | GET | cluster panel fragment |
| `/ui/login` | GET | login page |

### 4.3.2 API routes

| Route | Method | Purpose |
|---|---|---|
| `/healthz` | GET | health |
| `/api/documents` | GET | list documents |
| `/api/documents/{document_id}` | GET | metadata |
| `/api/documents/{document_id}/reader/branch-a` | GET | Branch A JSON or HTML partial |
| `/api/documents/{document_id}/reader/branch-c` | GET | Branch C JSON or HTML partial |
| `/api/documents/{document_id}/clusters` | GET | cluster metadata |
| `/api/documents/{document_id}/piece/{piece_id}` | GET | piece detail for tooltip |
| `/api/documents/{document_id}/jump/by-piece/{piece_id}` | GET | resolve transcript anchor |
| `/api/prefs` | GET/PUT | reader preferences |
| `/api/auth/session` | GET | current session info |

### 4.3.3 Frontend DOM contracts

This is critical for loose coupling between templates and JS.

#### Branch A piece span

```html
<span
  id="piece-p0001"
  class="piece-run"
  data-piece-id="p0001"
  data-cluster-id="c02"
  data-start-s="12.34"
  data-end-s="19.20"
>
  First piece text.
</span>
```

#### Branch C summary sentence

```html
<span
  id="summary-s0001"
  class="summary-sentence"
  data-sentence-id="s0001"
  data-cited-piece-ids="p0003,p0004,p0005"
>
  The speaker distinguishes lived perception from formal abstraction.
</span>
```

If the HTML emits these attributes exactly, the JS layer can remain small and deterministic.

---

## 5. Phase P0 — Skeleton, shell, and contracts

## 5.1 Goal

Boot the app, render a stable shell, and freeze contracts so parallel work can start.

## 5.2 Modules in scope

- L1 `core-contracts`
- shell routes/templates
- base settings and dependency container
- health endpoint
- static asset loading
- contract tests for schemas

## 5.3 Files to implement first

### 5.3.1 `requirements.txt`

Keep this minimal and Cloud Run friendly.

```txt
fastapi[standard]
jinja2
gunicorn
uvicorn-worker
pydantic
pydantic-settings
python-multipart
httpx
pytest
pytest-cov
```

### 5.3.2 root `main.py`

```python
# Root entrypoint used by Cloud Run / Gunicorn
from app.main import app
```

### 5.3.3 `Procfile`

```txt
web: gunicorn -b :$PORT -w 1 -k uvicorn_worker.UvicornWorker main:app
```

### 5.3.4 `app/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Transcript Renderer"
    app_env: str = "dev"
    log_level: str = "INFO"

    # Adapter selection:
    # - localfs for local dev
    # - gcs/firestore/firebase in cloud phases
    artifact_store_backend: str = "localfs"
    document_repo_backend: str = "localfs"
    preferences_repo_backend: str = "memory"
    auth_backend: str = "fake"

    # Local sample data roots
    sample_data_root: str = "./sample_data"
    render_output_root: str = "./sample_data/rendered"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

settings = Settings()
```

### 5.3.5 `app/main.py`

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.health import router as health_router
from app.routes.ui_shell import router as shell_router

app = FastAPI(title="Transcript Renderer")

app.include_router(health_router)
app.include_router(shell_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

### 5.3.6 `app/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
def healthz():
    return {"status": "ok"}
```

### 5.3.7 `app/routes/ui_shell.py`

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ui")
def ui_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={"page_title": "Transcript Renderer"},
    )
```

### 5.3.8 `app/templates/base.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{{ page_title or "Transcript Renderer" }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="/static/vendor/htmx.min.js"></script>
    <script defer src="/static/js/app.js"></script>
    <link rel="stylesheet" href="/static/css/app.css" />
  </head>
  <body>
    {% block body %}{% endblock %}
  </body>
</html>
```

### 5.3.9 `app/templates/pages/home.html`

```html
{% extends "base.html" %}
{% block body %}
<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar__title">Documents</div>
    <div class="sidebar__empty">Catalog not loaded yet.</div>
  </aside>

  <main class="main-pane">
    <header class="topbar">
      <h1>Transcript Renderer</h1>
    </header>
    <section class="hero-card">
      <p>Phase P0 complete when shell, CSS and JS load without errors.</p>
    </section>
  </main>
</div>
{% endblock %}
```

## 5.4 Validation steps

### Commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Open

- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/ui`

### Expected result

- `/healthz` returns `{"status": "ok"}`
- `/ui` renders shell
- browser devtools show no 404 for CSS/JS
- no server stack traces

## 5.5 Failure modes and interpretation

| Symptom | Likely cause | Action |
|---|---|---|
| `TemplateNotFound` | wrong template path | verify `app/templates` and route template names |
| static 404 | static mount path wrong | verify `app.mount("/static", ...)` |
| app boots but `/ui` 500s | Jinja context or template syntax error | inspect traceback, simplify template |
| shell loads without CSS | incorrect `<link>` path | verify `/static/css/app.css` exists |

## 5.6 Exit criteria

P0 is complete only if:
- contract schemas exist as stubs in `app/core/contracts`
- shell page renders
- dev server boot is stable
- at least one smoke test exists under `tests/routes`

---

## 6. Phase P1 — Local sample catalog and document loader

## 6.1 Goal

Use the uploaded sample artifacts as local placeholders so the app can show a real document list and open a document page without any cloud dependency.

## 6.2 Modules in scope

- L2 `catalog-and-storage`
- local sample extraction tool
- local document repository
- sidebar document list
- document open route

## 6.3 Key design decision

Do **not** bind the app directly to the zip layout.

Implement a small unpack/import tool that transforms the zip into a local dev-friendly structure under `sample_data/`.

This avoids scattering zip path knowledge all over the codebase.

## 6.4 Required local structure after import

```text
sample_data/
├── imported/
│   ├── sample01/
│   │   ├── source/
│   │   ├── a/
│   │   ├── b/
│   │   └── metadata.json
│   └── sample02/
└── rendered/
    └── sample01/
```

## 6.5 Implement the importer

### 6.5.1 `app/tools/unpack_sample_data.py`

```python
"""
Unpack the provided sample zip into a normalized local structure used by the app.

Responsibilities:
- read the original zip
- copy relevant files into sample_data/imported/<document_id>/
- create a metadata.json file per document
- never perform renderer-specific packaging here
- keep this step as a simple import/transcoding layer
"""

from __future__ import annotations
import json
import shutil
import zipfile
from pathlib import Path

def main(zip_path: str, out_root: str) -> None:
    # 1. Create output roots.
    # 2. Inspect original file names.
    # 3. Group by document/sample prefix.
    # 4. Copy relevant source files.
    # 5. Emit a normalized metadata.json for later stages.
    raise NotImplementedError("Implement importer")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--zip", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    main(args.zip, args.out)
```

## 6.6 Repository interface

### 6.6.1 `app/core/interfaces/document_repository.py`

```python
from __future__ import annotations
from typing import Protocol
from app.core.contracts.document_manifest import DocumentManifest

class DocumentRepository(Protocol):
    def list_documents(self, tenant_id: str) -> list[DocumentManifest]:
        ...

    def get_document(self, tenant_id: str, document_id: str) -> DocumentManifest:
        ...
```

### 6.6.2 Local implementation

```python
# app/adapters/localfs/document_repository.py
from pathlib import Path
import json

class LocalFsDocumentRepository:
    """
    Reads document manifests from local dev storage.
    This adapter is the reference implementation for repository behavior.
    Cloud adapters must match its semantics.
    """

    def __init__(self, root: str):
        self.root = Path(root)

    def list_documents(self, tenant_id: str):
        # Return stable order for repeatable UI and tests.
        raise NotImplementedError

    def get_document(self, tenant_id: str, document_id: str):
        raise NotImplementedError
```

## 6.7 Service layer

### 6.7.1 `app/services/document_catalog_service.py`

```python
class DocumentCatalogService:
    def __init__(self, repo):
        self.repo = repo

    def list_documents_for_sidebar(self, tenant_id: str) -> list[dict]:
        """
        Return a UI-focused catalog shape:
        - id
        - title
        - available views
        - updated_at if available
        - has_audio / has_clusters
        """
        raise NotImplementedError
```

## 6.8 UI routes and partials

### Sidebar route

```python
# app/routes/ui_documents.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ui/documents/sidebar")
def sidebar(request: Request):
    # Resolve tenant_id from fake session for now.
    # Call catalog service.
    # Render partials/sidebar.html
    raise NotImplementedError
```

### Sidebar partial

```html
<div class="sidebar__search">
  <input type="text" placeholder="Search documents" />
</div>

<ul class="doc-list">
  {% for doc in documents %}
    <li>
      <a href="/ui/documents/{{ doc.document_id }}">
        {{ doc.title }}
      </a>
    </li>
  {% endfor %}
</ul>
```

## 6.9 Validation steps

### Commands

```bash
python app/tools/unpack_sample_data.py --zip /path/to/data.zip --out ./sample_data
uvicorn app.main:app --reload
```

### Manual checks

- Sidebar lists the imported sample documents.
- Clicking a document opens `/ui/documents/{document_id}`.
- If render manifests are not yet built, the page shows a clear “not packaged yet” state instead of crashing.

### Expected visible result

A stable shell with:
- left sidebar containing imported documents
- a main pane showing document metadata

## 6.10 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| no docs appear | importer failed or repo path mismatch | inspect `sample_data/imported` |
| doc page 404 | route mismatch or missing document manifest | verify `document_id` emitted by repo |
| sidebar order unstable | filesystem iteration not sorted | enforce deterministic sort |

## 6.11 Exit criteria

P1 is complete only if:
- a developer can import the sample zip locally
- the UI lists those documents
- a document page opens without cloud services
- local repository contract tests exist

---

## 7. Phase P2 — Build normalized render manifests

## 7.1 Goal

Convert imported sample artifacts into renderer-ready manifests:
- `document_manifest.json`
- `pieces_index.json`
- `branch_a_render.json`
- `clusters_render.json`
- `branch_c_render.json` (real or fixture)
- `audio_manifest.json`

This phase is the keystone for the rest of the app.

## 7.2 Modules in scope

- L3 `manifest-packager`
- fixture generation for Branch C until real branch exists
- packager contract tests
- packager CLI tool

## 7.3 Packager responsibilities

The packager service must:
1. read imported source artifacts
2. resolve canonical pieces
3. build the `pieces_index`
4. build render plans for Branch A and Branch B overlay
5. build or seed Branch C render view
6. emit stable JSON to `sample_data/rendered/<document_id>/`

The packager must **not**:
- perform remote model calls
- modify upstream meaning
- invent timestamps
- parse UI state

## 7.4 Core service skeleton

### `app/services/manifest_packager_service.py`

```python
class ManifestPackagerService:
    """
    Read imported artifacts and emit render-ready normalized manifests.

    This service is pure application logic.
    It should not know whether files live on local disk or GCS.
    """

    def __init__(self, artifact_store):
        self.artifact_store = artifact_store

    def package_document(self, tenant_id: str, document_id: str) -> dict:
        """
        High-level orchestration:
        1. load source metadata
        2. load canonical pieces bundle
        3. build pieces_index
        4. build branch_a_render
        5. build clusters_render
        6. build branch_c_render (fixture if needed)
        7. build document_manifest
        8. persist all outputs
        9. return summary report
        """
        raise NotImplementedError
```

## 7.5 Recommended internal packager subfunctions

```python
def build_pieces_index(bundle_json: dict, piece_to_cluster: dict | None) -> dict:
    # Use canonical pieces as source of truth.
    # Every piece gets:
    # - piece_id
    # - timestamps
    # - text
    # - cluster_id or null
    # - dom_anchor
    raise NotImplementedError

def build_branch_a_render(a_markdown: str, pieces_index: dict) -> dict:
    # Parse the already-organized Branch A structure into blocks.
    # Do not attempt clever markdown reconstruction beyond what the branch already guarantees.
    # Output blocks with exact piece runs in original order.
    raise NotImplementedError

def build_clusters_render(cluster_json: dict, pieces_index: dict) -> dict:
    # Create UI-facing cluster metadata:
    # - cluster_id
    # - title
    # - color_token
    # - piece_ids
    raise NotImplementedError

def build_branch_c_render_from_fixture(pieces_index: dict) -> dict:
    # Temporary until real Branch C exists:
    # generate a deterministic summary fixture
    # OR read seeded fixture JSON prepared by app/tools/seed_fixture_branch_c.py
    raise NotImplementedError
```

## 7.6 Why a seeded Branch C fixture is acceptable now

Branch C is not implemented upstream yet, but the renderer contract can still be completed now.

That lets:
- summary reader UI work proceed independently
- jump logic be validated
- tooltip citation logic be validated
- final integration later become mostly a data swap

## 7.7 CLI wrapper

### `app/tools/build_render_manifests.py`

```python
from app.services.manifest_packager_service import ManifestPackagerService

def main(document_id: str | None = None):
    """
    Build manifests for one or all imported documents.
    This is the primary local validation entrypoint for P2 and later phases.
    """
    raise NotImplementedError
```

## 7.8 Validation steps

### Commands

```bash
python app/tools/unpack_sample_data.py --zip /path/to/data.zip --out ./sample_data
python app/tools/build_render_manifests.py
find ./sample_data/rendered -maxdepth 3 -type f | sort
```

### Expected result

For each imported document:
- render directory exists
- all expected JSON files exist
- JSON is valid
- repeated runs are deterministic

### Determinism check

```bash
python app/tools/build_render_manifests.py
find sample_data/rendered -type f -name '*.json' -print0 | xargs -0 sha256sum > /tmp/run1.txt
python app/tools/build_render_manifests.py
find sample_data/rendered -type f -name '*.json' -print0 | xargs -0 sha256sum > /tmp/run2.txt
diff -u /tmp/run1.txt /tmp/run2.txt
```

Expected:
- no diff unless source sample files changed

## 7.9 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| missing pieces in Branch A render | packager failed to align pieces | add explicit packager diagnostics showing orphaned piece IDs |
| malformed JSON | non-serializable object leaked from service | normalize types before write |
| repeated runs differ | non-deterministic ordering | sort everywhere before write |

## 7.10 Exit criteria

P2 is complete only if:
- all render manifests are generated locally
- repeated packaging is deterministic
- packager emits clear diagnostics for missing inputs
- P3/P4/P5 can be built entirely from these manifests

---

## 8. Phase P3 — Branch A reader, hover, tooltip, and audio overlay

## 8.1 Goal

Deliver the first fully compelling experience:
- open Branch A by default
- hover over a piece
- highlight that whole piece
- show tooltip with start/end timestamp and play action
- click play and start audio from that piece
- keep reading uninterrupted

## 8.2 Modules in scope

- L4 `reader-branch-a`
- reader service
- Branch A template partial
- tooltip API
- audio overlay JS and HTML
- minimal audio endpoint

## 8.3 Reader service contract

### `app/services/reader_service.py`

```python
class ReaderService:
    def __init__(self, artifact_store):
        self.artifact_store = artifact_store

    def load_branch_a(self, tenant_id: str, document_id: str) -> dict:
        # Load branch_a_render.json and pieces_index.json
        # Return a view model ready for Jinja.
        raise NotImplementedError

    def get_piece_tooltip(self, tenant_id: str, document_id: str, piece_id: str) -> dict:
        # Return:
        # - piece_id
        # - start_s
        # - end_s
        # - start_hms
        # - end_hms
        # - play_url
        raise NotImplementedError
```

## 8.4 UI rendering pattern

Each piece run is rendered as a span.

Example Jinja pattern:

```html
{% for block in branch_a.blocks %}
  {% if block.type in ["h1","h2","h3"] %}
    <{{ block.type }} id="{{ block.anchor }}">{{ block.text }}</{{ block.type }}>
  {% elif block.type == "paragraph" %}
    <p id="{{ block.anchor }}">
      {% for run in block.piece_runs %}
        <span
          id="piece-{{ run.piece_id }}"
          class="piece-run"
          data-piece-id="{{ run.piece_id }}"
          data-cluster-id="{{ run.cluster_id or '' }}"
          data-start-s="{{ run.start_s }}"
          data-end-s="{{ run.end_s }}"
        >{{ run.text }}</span>
      {% endfor %}
    </p>
  {% endif %}
{% endfor %}
```

## 8.5 Tooltip delivery choice

Use a lightweight **single tooltip container** managed by JS.  
Do not instantiate one tooltip component per piece.

Why:
- less DOM noise
- easier state control
- easier cluster interaction later

## 8.6 Reader JS responsibilities

### `app/static/js/reader.js`

```javascript
/**
 * Responsibilities:
 * - detect mouseenter/mouseleave on .piece-run
 * - highlight the hovered piece
 * - optionally color with cluster color if cluster overlay is enabled
 * - request tooltip payload only when needed
 * - place tooltip near cursor or near the piece bounds
 * - publish a custom event when user clicks "Play"
 * - support jump-to-piece when URL includes ?piece_id=...
 */
(function () {
  const state = {
    hoverEnabled: true,
    tooltipEnabled: true,
    clusterMode: "off", // off | hover-only | pinned
    activePieceId: null,
  };

  function bindPieceHover(container) {
    // Delegate events from the reader root.
    // Never bind listeners to every piece individually.
  }

  function showTooltipForPiece(pieceEl) {
    // Load tooltip content if not cached.
    // Render timestamps and Play link/button.
  }

  function setActivePiece(pieceId) {
    // Add/remove CSS class on the active piece.
  }

  window.TranscriptReader = {
    bindPieceHover,
    setActivePiece,
  };
})();
```

## 8.7 Audio overlay responsibilities

### `app/static/js/audio_player.js`

```javascript
/**
 * Responsibilities:
 * - create or manage a bottom overlay audio player
 * - seek to a timestamp
 * - start playback
 * - emit timeupdate-driven piece highlighting
 * - stay resilient if audio is unavailable
 */
(function () {
  const state = {
    audioEl: null,
    pieceTimeline: [],
  };

  function ensurePlayer() {}
  function loadDocumentAudio(audioUrl) {}
  function playFromSeconds(seconds) {}
  function syncHighlightToCurrentTime() {
    // Optional in P3: nearest-piece highlighting during playback.
  }

  window.TranscriptAudioPlayer = {
    ensurePlayer,
    loadDocumentAudio,
    playFromSeconds,
  };
})();
```

## 8.8 Routes

### Tooltip route

```python
@router.get("/api/documents/{document_id}/piece/{piece_id}")
def piece_tooltip(document_id: str, piece_id: str):
    # Return JSON used by the single tooltip container.
    raise NotImplementedError
```

### Audio page/partial route

```python
@router.get("/ui/documents/{document_id}/audio-overlay")
def audio_overlay(document_id: str):
    # Return partial that contains the audio element and controls.
    raise NotImplementedError
```

## 8.9 Validation steps

### Commands

```bash
uvicorn app.main:app --reload
# in another terminal if needed:
python app/tools/build_render_manifests.py
```

### Manual UI validation

Open a packaged document and verify:
1. Branch A is the default view.
2. Moving the mouse over a piece highlights the entire piece.
3. Tooltip shows start/end time.
4. Clicking play opens bottom overlay and begins from the piece start.
5. The UI remains readable when not hovering.

### Expected visible result

This is the first phase where the app already looks like the intended product.

## 8.10 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| only part of a piece highlights | piece DOM split incorrectly | verify paragraph rendering preserves one span per piece |
| tooltip flickers | mouseenter/mouseleave logic too granular | use delegated events and debounced hide |
| audio starts at 0 | timestamp parsing issue | inspect `data-start-s` and API payload |
| hover breaks reading | highlight style too strong | soften background/outline and reduce animation |

## 8.11 Exit criteria

P3 is complete only if:
- hover reliably highlights whole pieces
- tooltip is stable
- audio seek from piece start works
- branch A is pleasant to read without extra chrome

---

## 9. Phase P4 — Branch B cluster overlays

## 9.1 Goal

Add topic-awareness without polluting the default reading view.

Cluster colors are not always visible. They only appear when:
- cluster mode is enabled
- the user hovers a piece
- or a cluster is pinned

## 9.2 Modules in scope

- L5 `reader-clusters`
- cluster panel partial
- cluster state JS
- cluster color token system
- pinned cluster logic

## 9.3 State model

```javascript
const clusterState = {
  enabled: false,
  pinnedClusterIds: new Set(),
  hoverClusterId: null,
  colorOverrides: {}, // cluster_id -> color_token
};
```

## 9.4 Cluster panel contract

The cluster panel receives:

```json
{
  "clusters": [
    {
      "cluster_id": "c02",
      "title": "Phenomenology of perception",
      "color_token": "violet",
      "piece_count": 18
    }
  ]
}
```

The panel must support:
- single hover
- single click toggle
- multiple pinned clusters
- double-click color edit

## 9.5 CSS contract

Use CSS custom properties instead of hard-coded classes for every possible cluster.

Example:

```css
:root {
  --cluster-violet: rgba(139, 92, 246, 0.22);
  --cluster-emerald: rgba(16, 185, 129, 0.22);
  --cluster-amber: rgba(245, 158, 11, 0.22);
}

.piece-run.is-active {
  background: rgba(59, 130, 246, 0.10);
}

.piece-run.cluster-violet.is-cluster-visible {
  background: var(--cluster-violet);
}
```

## 9.6 JS responsibilities

### `app/static/js/clusters.js`

```javascript
/**
 * Responsibilities:
 * - manage cluster enabled/disabled state
 * - apply cluster colors to hovered piece
 * - apply cluster colors to all pieces for pinned clusters
 * - update panel state
 * - persist preference via /api/prefs
 */
(function () {
  function toggleClusterPanel() {}
  function setClusterMode(enabled) {}
  function pinCluster(clusterId) {}
  function unpinCluster(clusterId) {}
  function applyClusterStyles() {}

  window.TranscriptClusters = {
    toggleClusterPanel,
    setClusterMode,
    pinCluster,
    unpinCluster,
  };
})();
```

## 9.7 Validation steps

### Manual UI validation

1. Open document.
2. Enable “show clusters”.
3. Hover a piece:
   - highlight still works
   - color reflects that piece’s cluster
4. Hover a cluster title:
   - all matching pieces highlight
5. Click a cluster title:
   - highlight remains pinned
6. Click a second cluster:
   - both stay visible
7. Disable cluster mode:
   - all cluster styles disappear, base reader remains clean

## 9.8 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| pinned highlights never clear | state cleanup bug | treat DOM recompute as source of truth |
| cluster hover is slow | too many DOM writes | batch updates with `requestAnimationFrame` |
| reader becomes unreadable | colors too saturated | reduce alpha and border emphasis |

## 9.9 Exit criteria

P4 is complete only if:
- default reader remains clean
- cluster mode feels additive rather than intrusive
- multi-cluster pinning works
- preference state can be restored on reload

---

## 10. Phase P5 — Branch C reader and cross-view navigation

## 10.1 Goal

Deliver the grounded summary experience:
- open summary view
- hover summary sentence
- show cited pieces
- click cited piece
- jump to Branch A at that piece
- from there use existing hover/audio behavior

## 10.2 Modules in scope

- L6 `reader-branch-c`
- summary partial
- sentence tooltip or inline popover
- cross-link resolver
- transcript jump handler

## 10.3 Branch C rendering contract

The UI must treat each summary sentence as a first-class object, not as loose prose with textual cites.

Template example:

```html
{% for block in branch_c.blocks %}
  {% if block.type == "summary_sentence" %}
    <span
      id="{{ block.dom_anchor }}"
      class="summary-sentence"
      data-sentence-id="{{ block.sentence_id }}"
      data-cited-piece-ids="{{ block.cited_piece_ids | join(',') }}"
    >{{ block.text }}</span>
  {% endif %}
{% endfor %}
```

## 10.4 Crosslink service

### `app/services/crosslink_service.py`

```python
class CrosslinkService:
    def __init__(self, artifact_store):
        self.artifact_store = artifact_store

    def resolve_summary_sentence(self, tenant_id: str, document_id: str, sentence_id: str) -> dict:
        """
        Return:
        - sentence text
        - cited pieces with timestamps
        - branch-a jump urls
        """
        raise NotImplementedError

    def build_branch_a_jump_url(self, document_id: str, piece_id: str) -> str:
        return f"/ui/documents/{document_id}/branch-a?piece_id={piece_id}"
```

## 10.5 Jump behavior

When Branch A loads with `?piece_id=p0005`:
- scroll that piece into view
- temporarily pulse the piece
- keep hover/audio behavior intact
- optionally auto-open tooltip if `?autotooltip=1`

This behavior must be implemented client-side in `reader.js`.

## 10.6 Validation steps

### Manual UI validation

1. Open summary view.
2. Hover a summary sentence.
3. Tooltip/popover lists cited pieces.
4. Click a cited piece.
5. New tab or same-tab branch-A navigation lands near the right piece.
6. The piece pulses briefly to show the jump target.
7. Hover piece and press play to confirm end-to-end traceability.

## 10.7 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| summary sentence has no cites | fixture or real Branch C render malformed | validate `cited_piece_ids` non-empty in contract tests |
| jump lands on wrong transcript area | bad `piece_id` / DOM anchor mismatch | ensure `dom_anchor` in `pieces_index` matches rendered IDs |
| new tab opens but no pulse | query parsing missing in JS init | add a startup URL handler |

## 10.8 Exit criteria

P5 is complete only if:
- summary sentences expose citations
- citation click lands on the right transcript piece
- traceability path summary → transcript → audio is demonstrably working

---

## 11. Phase P6 — Authentication, ownership, and saved preferences

## 11.1 Goal

Add user accounts and isolate document access by user.

## 11.2 Modules in scope

- L7 `auth-and-prefs`
- Firebase auth frontend integration
- Firebase Admin token verification in backend
- user-scoped repository queries
- reader preference persistence

## 11.3 Auth strategy

Use:
- Firebase Auth in frontend
- ID token sent to backend
- backend verifies token through adapter
- backend stores/reads preferences keyed by `tenant_id`

### Why this split

- browser sign-in UX is easy
- backend remains authoritative for access control
- no custom password storage
- easy switch between fake auth in local dev and Firebase in cloud

## 11.4 Auth verifier contract

```python
class AuthVerifier(Protocol):
    def verify_request(self, request) -> dict:
        """
        Return an auth context:
        {
          "tenant_id": "...",
          "user_id": "...",
          "email": "...",
          "is_authenticated": True
        }
        """
        ...
```

Local dev:
- `FakeAuthVerifier` returns `tenant_id="local-dev"`

Cloud:
- `FirebaseAuthVerifier` verifies bearer token or session cookie

## 11.5 Preferences contract

```python
{
  "tenant_id": "user_123",
  "cluster_mode_enabled": true,
  "tooltip_enabled": true,
  "hover_enabled": true,
  "cluster_color_overrides": {
    "c02": "emerald"
  }
}
```

## 11.6 Validation steps

### Local fake-auth validation

- app still works with `APP_AUTH_BACKEND=fake`
- preferences survive reload using an in-memory or local file repo

### Cloud-auth validation later

- sign in with Google
- sign in with email/password
- backend sees authenticated session
- one user cannot list another user’s documents

## 11.7 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| signed-in user still sees fake tenant docs | dependency injection still points to fake auth | verify environment-dependent adapter selection |
| prefs save but do not load | repo write/read key mismatch | standardize `tenant_id` primary key |
| backend accepts unauthenticated request | auth dependency not mounted on route | require auth dependency on protected routes |

## 11.8 Exit criteria

P6 is complete only if:
- there is a clean fake-auth path for local dev
- there is a clean Firebase path for cloud
- preferences persist and restore
- repositories are tenant-scoped

---

## 12. Phase P7 — Cloud adapters and async extension points

## 12.1 Goal

Swap local adapters with cloud adapters without changing service logic.

## 12.2 Modules in scope

- L8 `cloud-adapters`
- GCS artifact store
- Firestore document repository
- Firestore preferences repository
- optional async hooks for packaging or later ingestion

## 12.3 Artifact store contract

```python
class ArtifactStore(Protocol):
    def read_json(self, path: str) -> dict: ...
    def write_json(self, path: str, payload: dict) -> None: ...
    def read_text(self, path: str) -> str: ...
    def write_text(self, path: str, content: str) -> None: ...
    def exists(self, path: str) -> bool: ...
    def signed_media_url(self, path: str, ttl_seconds: int = 900) -> str: ...
```

Local and GCS adapters must behave the same from the service layer’s point of view.

## 12.4 GCS adapter notes

- app should not directly expose bucket paths
- media/audio should be proxied or served via signed URLs
- write paths must be namespaced by tenant and document

Example path convention:

```text
gs://<bucket>/tenants/<tenant_id>/documents/<document_id>/render/branch_a_render.json
gs://<bucket>/tenants/<tenant_id>/documents/<document_id>/media/audio/source.mp3
```

## 12.5 Firestore repository notes

Use Firestore only for:
- document catalog metadata
- ownership
- preference data
- ingestion/job state later

Do **not** store large render JSON blobs inside Firestore.  
Keep large artifacts in GCS.

## 12.6 Validation steps

- switch local adapters to GCS/Firestore in a staging environment
- run the same contract tests against both backends
- use smoke test route to load one document end-to-end

## 12.7 Exit criteria

P7 is complete only if:
- services are backend-agnostic
- local and cloud adapters satisfy the same tests
- a cloud environment can load the same app without codepath forks in the service layer

---

## 13. Parallel work packages

Use this section to split work across developers.

## 13.1 Work package A — Contracts + packager

**Owns**
- `app/core/contracts/*`
- `app/services/manifest_packager_service.py`
- `app/tools/build_render_manifests.py`
- packager contract tests

**Inputs required**
- sample zip and architecture report

**Outputs promised**
- valid manifests under `sample_data/rendered`
- schema examples
- deterministic packager behavior

**Blocks**
- P3, P4, P5 if delayed

## 13.2 Work package B — Shell + catalog + Branch A reader

**Owns**
- shell templates
- sidebar
- document routes
- reader partials
- reader.js
- audio overlay

**Inputs required**
- frozen manifest contracts
- packaged Branch A outputs

**Outputs promised**
- usable reader UI
- piece hover and tooltip working

## 13.3 Work package C — Clusters + summary cross-links

**Owns**
- cluster panel
- clusters.js
- summary partial
- crosslink service
- jump behavior

**Inputs required**
- `clusters_render.json`
- `branch_c_render.json`

**Outputs promised**
- cluster overlay
- summary → transcript jumps

## 13.4 Work package D — Auth + cloud adapters

**Owns**
- auth adapter(s)
- Firestore repo
- GCS artifact store
- preference persistence

**Inputs required**
- frozen repository interfaces
- infrastructure enablement progress

**Outputs promised**
- user-scoped app in cloud
- preference persistence

---

## 14. Mandatory test strategy

## 14.1 Contract tests

Each contract file gets:
- parse valid sample
- reject malformed required fields
- deterministic serialization

## 14.2 Service tests

Mock adapters and test:
- document catalog
- packager
- reader tooltip resolution
- crosslink resolution

## 14.3 Route tests

Use FastAPI `TestClient` for:
- `/healthz`
- `/api/documents`
- `/ui/documents/{document_id}`
- tooltip endpoint
- jump endpoint

## 14.4 E2E tests

At minimum:
1. open Branch A
2. hover piece
3. show tooltip
4. play audio
5. switch to summary
6. click cited piece
7. land on transcript target

Even one Playwright script that covers this path is enough for the PoC.

---

## 15. Acceptance checklist for the whole application

The application is implementation-complete for this PoC only if all items below are true:

- [ ] App boots locally with no cloud services
- [ ] Sample zip can be imported into local dev storage
- [ ] Render manifests can be built deterministically
- [ ] Sidebar lists documents
- [ ] Branch A loads by default
- [ ] Hover highlights a whole piece
- [ ] Tooltip shows exact timestamps
- [ ] Audio overlay plays from the piece start
- [ ] Cluster overlay is toggleable and non-intrusive
- [ ] Multiple clusters can be pinned
- [ ] Summary sentences expose cited pieces
- [ ] Summary click jumps to the correct transcript piece
- [ ] Reader preferences persist
- [ ] User access is tenant-scoped
- [ ] Local and cloud adapters satisfy the same contracts

---

## 16. Recommended implementation order inside a small team

If only one developer:
1. P0
2. P1
3. P2
4. P3
5. P5
6. P4
7. P6
8. P7

If two developers:
- Dev A: P0 → P2 → P5
- Dev B: P1 → P3 → P4
- then both converge on P6/P7

If three developers:
- Dev A: contracts + packager
- Dev B: Branch A reader + audio
- Dev C: clusters + summary + jump logic
- shared merge point: auth + cloud adapters

---

## 17. What the developer should not improvise

These are explicit “do not drift” rules.

- Do not parse final UX behavior from markdown string heuristics at runtime.
- Do not mix Firestore large artifact blobs with metadata.
- Do not make templates infer missing timestamps.
- Do not bypass service interfaces from routes.
- Do not make JS depend on invisible template conventions not documented here.
- Do not ship cluster colors always-on by default.
- Do not make auth optional on protected cloud routes.
- Do not couple local file paths into service logic.

---

## 18. Handoff summary

A developer receiving:
- this implementation plan
- `congress_renderer_architecture_report.md`
- `transcript_renderer_infrastructure_enablement_guide.md`
- the sample data zip

should be able to build the PoC with low ambiguity.

This document is intentionally biased toward:
- clear seams
- deterministic behavior
- visible progress at every phase
- local-first validation before cloud integration
