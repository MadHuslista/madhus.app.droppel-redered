# Transcript Renderer — Practical Implementation Map

Version: 2026-03-08  
Scope: execution-ready refinement of the existing `.augment/` request and planning documents  
Companion documents:
- `../requests/renderer.md`
- `transcript_renderer_architecture_report.md`
- `transcript_renderer_implementation_plan.md`
- `transcript_renderer_infrastructure_enablement_guide.md`

---

## Document Purpose

This report translates the existing project request and planning documents into a practical implementation map for the transcript renderer project.

It does **not** replace the prior documents. Instead, it refines them into an execution-oriented guide that makes the next implementation steps obvious, dependency-aware, and suitable for modular delivery.

This document is specifically intended to answer:

- what should be implemented first,
- which seams must be frozen before parallel work starts,
- how the `data/` artifacts map into renderer-facing modules,
- and which ambiguities still require explicit decisions before implementation proceeds.

---

## Relation to Existing `.augment/` Documents

### How this report fits into the current document set

| Document                                                 | What it already defines                                                                                             | What gap remains                                                                                       | How this report fills the gap                                                               |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `../requests/renderer.md`                                | Product intent, UX goals, branch semantics, desired user flows, and PoC expectations                                | It is product-rich but not execution-ordered                                                           | Converts the request into a dependency-aware build sequence and implementation seams        |
| `transcript_renderer_architecture_report.md`             | Recommended stack, infrastructure, contracts, architecture principles, module taxonomy, and packager-first strategy | It is architecture-correct but still broad at the implementation handoff level                         | Narrows the architecture into concrete near-term module priorities and practical sequencing |
| `transcript_renderer_implementation_plan.md`             | Repository structure, phased plan, module lanes, contracts, route ideas, tests, and work packages                   | It is detailed, but still partly phase-oriented rather than “what to do next in the codebase tomorrow” | Reframes the plan into a practical execution map centered on the highest-value path         |
| `transcript_renderer_infrastructure_enablement_guide.md` | Cloud foundation, service choices, environment sequencing, and local-to-cloud test ladder                           | It intentionally avoids code-level sequencing                                                          | Keeps infrastructure later in the sequence unless and until the code seams are stable       |

### What this report adds without contradicting the others

This report adds four practical layers that are only implicit in the current documents:

1. **A pipeline-artifact-to-renderer map** for the current `data/` samples.
2. **A build order optimized for lowest risk and fastest visible value**.
3. **A seam-freezing checklist** that must be completed before parallel work begins.
4. **A safest interpretation of ambiguous or unevenly mature areas**, especially Branch B and Branch C.

---

## Business Logic Summary

### Core business logic

The core business logic of the project is:

- transform audio transcription output into **canonical timestamped semantic pieces**,
- derive multiple user-facing views from those same pieces,
- preserve traceability from every view back to the original audio,
- and make cross-view navigation frictionless.

### Shared-source-of-truth principle

The central architectural rule, already established in the existing reports, is:

**canonical pieces are the shared source of truth**.

That means:

- Whisper words are the timing substrate.
- SAT segmentation creates semantic pieces.
- the canonical bundle assigns each piece stable identity and timestamps.
- Branch A, Branch B, and Branch C are **views over the same piece set**, not independent truths.

### Why this matters for implementation

If the implementation keeps canonical pieces as the stable reference point, then all high-value interactions remain deterministic:

- transcript piece → timestamps,
- transcript piece → audio seek,
- piece → cluster,
- summary sentence → cited pieces,
- citation click → transcript anchor,
- playback time → active piece highlight.

If this rule is violated, the renderer becomes a fragile markdown parser rather than a grounded document interface.

---

## Implementation Principles

### Principle 1 — Runtime consumes packaged render artifacts, not raw pipeline outputs

The renderer should not directly parse:

- raw Whisper JSON,
- raw SAT split JSON,
- raw model output for title trees,
- raw Branch B stage directories,
- or markdown with embedded piece hints.

Those belong to ingestion and packaging.

The runtime should consume normalized contracts such as:

- `document_manifest.json`
- `pieces_index.json`
- `branch_a_render.json`
- `branch_c_render.json`
- `clusters_render.json`
- `audio_manifest.json`

### Principle 2 — Absorb complexity in the packager, not in the UI

The UI should be thin and deterministic.

The packager should resolve:

- raw sample layout differences,
- heading/paragraph interleaving,
- cluster normalization,
- summary citation grounding,
- and audio metadata colocation.

### Principle 3 — Local-first implementation remains the default

The implementation should first succeed against local sample artifacts and local adapters.

Cloud integration is later work and should follow stable contracts, not drive them.

### Principle 4 — First ship the traceability loop, then enrich it

The first meaningful end-to-end product loop is:

1. open Branch A,
2. hover a piece,
3. inspect timestamps,
4. play audio from the piece,
5. later open Branch C,
6. jump from summary sentence to transcript piece,
7. then add clusters as an overlay.

This sequence validates the project’s real value before auth, library management, upload, or sync.

---

## Pipeline Artifact to Renderer Module Map

### Current `data/` folders and how they should be used

| Source path                      | Current meaning                                                           | Implementation role                                                       | Renderer-facing consumer  | Runtime source? |
| -------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------- | --------------- |
| `data/n06_whisper/`              | Whisper output with `words[]` and timestamps                              | Timing provenance and fallback validation input                           | Packager only             | No              |
| `data/p02_split_SaT/`            | SAT segmentation into semantic pieces                                     | Upstream segmentation input; useful for validation and importer context   | Packager only             | No              |
| `data/p03_build_cannon_bundle/`  | Canonical bundle of `piece_id`, text, start/end times                     | Primary packager input for `pieces_index` and audio timeline              | `ManifestPackagerService` | No              |
| `data/a1_tittle_tree/`           | Branch A structure proposal: title tree + paragraph breaks + piece ranges | Primary input for Branch A render planning                                | `ManifestPackagerService` | No              |
| `data/a2_recompose_md/`          | Human-facing Branch A markdown                                            | Validation/debug artifact only; should not be the runtime source of truth | QA and parity checks      | No              |
| `data/b1_clusters/*/stage5_out/` | Finalized Branch B cluster metadata and piece mappings                    | Primary input for `clusters_render.json`                                  | `ManifestPackagerService` | No              |
| `data/b1_clusters/*/stage6_out/` | Tentative final Branch B markdown                                         | Validation/debug artifact only                                            | QA and parity checks      | No              |
| future Branch C artifact         | Grounded summary with citations to pieces                                 | Primary input for `branch_c_render.json`                                  | `ManifestPackagerService` | No              |

### Practical interpretation of the current sample data

The sample data shows that some artifact variants are stronger than others.

For example:

- some Branch B sample directories contain empty final outputs,
- other variants contain usable `piece_to_cluster` and labeled cluster data,
- Branch A is materially more stable than Branch B,
- Branch C is not yet present as a stable upstream artifact.

### Safest implementation interpretation

For implementation purposes, treat each sample variation as an explicit artifact family, not as interchangeable truth.

Near-term safest behavior:

- use the canonical bundle as the real source of piece identity,
- use Branch A title-tree output as the structural source for transcript rendering,
- use the **non-empty** Branch B finalized outputs as the reference semantics for clusters,
- and use a **seeded Branch C fixture** until real upstream Branch C artifacts exist.

---

## Contracts and Seams That Must Be Stabilized First

Before parallel implementation begins, the following seams must be frozen.

### 1. Identity seam

The following identifiers must be stable and documented:

- `document_id`
- `source_bundle_id`
- `tenant_id`
- `piece_id`
- `cluster_id`
- `sentence_id`

Implementation rule:

- `piece_id` is the anchor of all cross-view behavior.
- no renderer behavior should depend on textual matching when an ID exists.

### 2. Render manifest seam

The minimal runtime contracts that must be frozen before the UI grows are:

- `document_manifest.json`
- `pieces_index.json`
- `branch_a_render.json`
- `audio_manifest.json`

The following can follow immediately after, but still before richer feature growth:

- `branch_c_render.json`
- `clusters_render.json`

### 3. Adapter seam

Service logic should only depend on repository/store interfaces such as:

- `ArtifactStore`
- `DocumentRepository`
- `PreferencesRepository`
- `AuthVerifier`

Routes should not bypass these seams.

### 4. DOM seam

The frontend and template contracts must be frozen for:

- Branch A piece spans,
- Branch C sentence spans,
- tooltip target lookup,
- cluster highlight lookup,
- query-string-driven jump behavior.

If DOM attributes drift casually, JS becomes brittle.

### 5. Sample import seam

The app should not embed assumptions about the raw `data/` folder directly into runtime logic.

The packager or importer must define one normalized local sample layout, and the rest of the app should consume only that normalized layout.

---

## Implementation Layers and Phases

This section reorders the existing planning into the highest-value, lowest-risk implementation path.

### Phase 0 — Freeze contracts and local sample normalization

#### Objective

Make it safe for implementation to start without cloud or runtime guessing.

#### Must exist before moving on

- contract schemas for runtime artifacts
- normalized local sample import model
- clear document identity and variant strategy
- deterministic write locations for rendered artifacts

#### Deliverables

- schema stubs under `app/core/contracts/`
- importer or sample loader contract
- deterministic output convention under `sample_data/rendered/<document_id>/`

### Phase 1 — Build the renderer packaging layer

#### Objective

Create the anti-corruption layer between pipeline artifacts and the web app.

#### Why this is first

Everything user-visible depends on it.

It unblocks:

- Branch A reader,
- audio interaction,
- Branch C jump logic,
- cluster overlays,
- contract tests,
- local and cloud adapter parity.

#### Deliverables

- `ManifestPackagerService`
- `build_render_manifests.py`
- generated `document_manifest.json`
- generated `pieces_index.json`
- generated `branch_a_render.json`
- generated `audio_manifest.json`
- seeded `branch_c_render.json`
- generated `clusters_render.json` when source data is usable

### Phase 2 — Implement the Branch A transcript reader

#### Objective

Deliver the first real reading surface using packaged Branch A output.

#### Deliverables

- document page route
- Branch A reader template/partial
- piece spans with deterministic dataset attributes
- document loading service for packaged outputs

#### Visible success

- user opens a document and sees a structured transcript by default

### Phase 3 — Implement hover, tooltip, and audio seek flow

#### Objective

Complete the first full traceability loop.

#### Deliverables

- tooltip endpoint and client logic
- bottom audio overlay
- play-from-piece interaction
- active-piece highlighting during playback

#### Visible success

- hover a piece,
- inspect exact timestamps,
- click play,
- audio starts at the right time.

### Phase 4 — Implement Branch C grounded summary navigation

#### Objective

Prove the second major value loop: summary → transcript → audio.

#### Deliverables

- Branch C render contract and seeded fixture path
- summary template/partial
- sentence tooltip/popover for citations
- crosslink service
- transcript jump handling from `piece_id`

#### Why this comes before Branch B overlay in practice

This order best validates the project’s core business value: grounded navigation.

It also matches the small-team recommendation in `transcript_renderer_implementation_plan.md`, even though the numbered phases in that document list Branch B before Branch C.

### Phase 5 — Implement Branch B cluster overlay

#### Objective

Add semantic topic awareness as an overlay, not as the foundation of reading.

#### Deliverables

- `clusters_render.json`
- cluster panel partial
- cluster state JS
- hover and pin behavior
- color override model

#### Why this is later

Clusters are valuable, but not required to validate transcript/audio/summary traceability.

### Phase 6 — Add preferences, auth, and library management

#### Objective

Move from demo-like local use toward user-scoped application behavior.

#### Deliverables

- preferences repository
- fake auth in local mode
- Firebase auth in cloud mode
- document sidebar/library
- tenant-scoped repositories

### Phase 7 — Add cloud adapters and deployment path

#### Objective

Swap local adapters for GCS/Firestore/Firebase without altering service logic.

#### Deliverables

- cloud artifact store
- Firestore-backed repositories
- Cloud Run staging deployment
- contract parity across local and cloud backends

### Phase 8 — Defer upload, sync, and orchestration until after the reader works

#### Objective

Only after the renderer is proven should the system add document ingestion and automation features.

#### Deferred features

- upload audio
- processing status UI
- Google Drive sync
- background ingestion orchestration

---

## Module-by-Module Implementation Map

### Highest-priority modules

| Module                                      | First responsibility                                | Depends on                        | Unblocks                             |
| ------------------------------------------- | --------------------------------------------------- | --------------------------------- | ------------------------------------ |
| `app/core/contracts/document_manifest.py`   | Define runtime document metadata contract           | identity rules                    | document loading and library listing |
| `app/core/contracts/pieces_index.py`        | Define canonical runtime piece lookup               | canonical bundle interpretation   | tooltips, audio, clusters, jumps     |
| `app/core/contracts/branch_a_render.py`     | Define deterministic transcript render blocks       | Branch A structure rules          | transcript UI                        |
| `app/core/contracts/audio_manifest.py`      | Define audio source contract                        | document/media strategy           | playback overlay                     |
| `app/core/contracts/branch_c_render.py`     | Define summary sentence and citation contract       | seeded or upstream Branch C       | summary navigation                   |
| `app/core/contracts/clusters_render.py`     | Define cluster overlay contract                     | Branch B normalization            | cluster UI                           |
| `app/services/manifest_packager_service.py` | Build runtime manifests from sample artifacts       | all runtime contracts             | everything UI-facing                 |
| `app/tools/build_render_manifests.py`       | CLI entry for deterministic packaging               | packager service                  | local validation loop                |
| `app/services/document_loader_service.py`   | Load packaged documents from artifact store         | manifests on disk/store           | routes and templates                 |
| `app/services/reader_service.py`            | Build Branch A and later Branch C view models       | packaged outputs                  | reader templates                     |
| `app/services/audio_service.py`             | Resolve playable audio metadata and timelines       | `pieces_index`, `audio_manifest`  | audio overlay                        |
| `app/services/crosslink_service.py`         | Resolve summary sentence citations into piece jumps | `branch_c_render`, `pieces_index` | Branch C UX                          |
| `app/services/cluster_service.py`           | Load cluster metadata for panel/highlighting        | `clusters_render`                 | Branch B overlay                     |

### First template and UI modules to implement

| Module                                        | First responsibility                         | Must be stable           |
| --------------------------------------------- | -------------------------------------------- | ------------------------ |
| `app/templates/pages/document.html`           | Main reader shell for one document           | yes                      |
| `app/templates/partials/reader_branch_a.html` | Transcript rendering from packaged Branch A  | yes                      |
| `app/templates/partials/audio_overlay.html`   | Persistent bottom playback UI                | yes                      |
| `app/static/js/reader.js`                     | Piece hover, tooltip, jump-to-piece handling | yes                      |
| `app/static/js/audio_player.js`               | Audio overlay state and piece-sync behavior  | yes                      |
| `app/templates/partials/reader_branch_c.html` | Summary rendering from packaged Branch C     | shortly after            |
| `app/static/js/clusters.js`                   | Cluster hover/pin/color logic                | after summary path works |
| `app/templates/partials/cluster_panel.html`   | Cluster label and pinning UI                 | after summary path works |

### First adapter modules to implement

| Module                                          | Immediate implementation mode | Notes                                                       |
| ----------------------------------------------- | ----------------------------- | ----------------------------------------------------------- |
| `app/adapters/localfs/artifact_store.py`        | required first                | reference behavior for all later backends                   |
| `app/adapters/localfs/document_repository.py`   | required first                | stable local catalog behavior                               |
| `app/adapters/localfs/sample_loader.py`         | required first                | hides raw `data/` layout differences                        |
| `app/adapters/firestore/document_repository.py` | later                         | only after local contracts are stable                       |
| `app/adapters/gcs/artifact_store.py`            | later                         | only after runtime artifact shapes are frozen               |
| `app/adapters/firebase/auth_verifier.py`        | later                         | only after fake auth and tenant-scoping behavior are stable |

---

## Contracts and Data-Flow Map

### End-to-end data flow

1. `n06_whisper` provides word-level timestamps.
2. `p02_split_SaT` provides piece segmentation.
3. `p03_build_cannon_bundle` yields canonical piece identity + timing.
4. `a1_tittle_tree` provides Branch A structure hints.
5. `b1_clusters/.../stage5_out` provides cluster membership and labels when available.
6. future Branch C data or seeded fixture provides summary sentences and piece citations.
7. `ManifestPackagerService` emits normalized runtime contracts.
8. runtime services load only normalized contracts.
9. templates emit explicit DOM attributes.
10. JS uses IDs and dataset attributes to coordinate hover, jump, and playback.

### Contract ownership

| Contract                 | Produced by                        | Consumed by                                          |
| ------------------------ | ---------------------------------- | ---------------------------------------------------- |
| `document_manifest.json` | packager                           | catalog, loader, routing layer                       |
| `pieces_index.json`      | packager                           | tooltip service, audio service, clusters, crosslinks |
| `branch_a_render.json`   | packager                           | Branch A reader                                      |
| `audio_manifest.json`    | packager                           | audio overlay and media route logic                  |
| `branch_c_render.json`   | packager or seeded fixture builder | Branch C reader and crosslink service                |
| `clusters_render.json`   | packager                           | cluster service and cluster UI                       |

### DOM ownership

| DOM element            | Required data                                                   | Consumer                                      |
| ---------------------- | --------------------------------------------------------------- | --------------------------------------------- |
| Branch A piece span    | `data-piece-id`, `data-start-s`, `data-end-s`, cluster metadata | `reader.js`, `audio_player.js`, `clusters.js` |
| Branch C sentence span | `data-sentence-id`, `data-cited-piece-ids`                      | `reader.js`, summary popover logic            |
| cluster panel item     | `data-cluster-id`, color token                                  | `clusters.js`                                 |

---

## Dependency-Aware Task Breakdown

### Task group A — Freeze contracts and sample normalization

#### Must be completed first

- define runtime schemas,
- define sample import/load conventions,
- choose document variant strategy,
- choose rendered output directory strategy.

#### Why it matters

Without this, packager logic and UI work will both guess at structure.

### Task group B — Build the packager and manifest tests

#### Depends on

- Task group A

#### Must deliver

- deterministic manifest generation
- reference packaged sample documents
- validation failures for missing or malformed source artifacts

#### Blocks

- Branch A UI,
- audio interaction,
- Branch C jump flow,
- cluster overlay.

### Task group C — Build Branch A reader and audio flow

#### Depends on

- Task group B

#### Must deliver

- document page
- Branch A render partial
- tooltip API
- audio overlay seek behavior

#### Visible product milestone

- first convincing transcript study experience

### Task group D — Build Branch C summary navigation

#### Depends on

- Task group B
- preferably Task group C, because summary targets the transcript reader

#### Must deliver

- summary rendering
- citation resolution
- jump-to-piece behavior

### Task group E — Build Branch B overlay

#### Depends on

- Task group B
- preferably Task group C for shared piece/highlight mechanics

#### Must deliver

- cluster panel
- hover and pinning
- piece-to-cluster highlighting

### Task group F — Build auth, preferences, and catalog persistence

#### Depends on

- local reader behavior being stable
- repository interfaces being frozen

#### Must deliver

- tenant-scoped repositories
- preference persistence
- real auth path in cloud

### Task group G — Build cloud adapters and deployment

#### Depends on

- all prior service seams being stable

#### Must deliver

- backend-agnostic services
- cloud-backed artifacts and metadata
- Cloud Run-hosted staging path

---

## Conceptually Defined vs Still Requiring Decisions

### Already conceptually defined

These areas are defined well enough to implement:

- **canonical pieces as SSOT**
- **packager-first architecture**
- **FastAPI + Jinja2 + HTMX modular monolith**
- **Cloud Run + GCS + Firestore + Firebase Auth** as the recommended infra path
- **Branch A as the default initial reader view**
- **hover → piece → tooltip → audio** as the first core user loop
- **Branch C as grounded sentence-level navigation**
- **auth/library/upload/sync as later layers**

### Still requiring explicit design decisions

| Topic                                           | Why it still needs a decision                  | Safest implementation interpretation                                                                 |
| ----------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| sample variation selection (`a`, `b`, `c`, `d`) | multiple artifacts exist for one source family | treat each variation as a separate importable document variant unless a canonical winner is declared |
| real Branch C artifact shape                    | upstream Branch C is not yet implemented       | use seeded fixture data behind the final `branch_c_render.json` contract                             |
| Branch B stability                              | some final sample outputs are empty            | normalize only from finalized non-empty stage outputs and fail clearly when unavailable              |
| exact audio serving strategy                    | proxy vs signed URL remains later-cloud detail | keep local media route simple; abstract signed URL support behind `ArtifactStore`                    |
| playback highlighting granularity               | word-level karaoke is attractive but costly    | first implement piece-level active highlighting only                                                 |
| cluster color palette rules                     | behavior is described, palette policy is not   | use small predefined token palette with local override storage                                       |

### Existing-document inconsistency to note explicitly

There is a mild sequencing inconsistency across the current planning documents:

- the implementation plan numbers Branch B before Branch C,
- the small-team recommendation in that same document puts Branch C before Branch B,
- the architecture report treats cluster highlighting as optional in the early reader slice.

### Safest interpretation for implementation

The safest implementation order is:

1. packaging layer,
2. Branch A reader,
3. hover/tooltip/audio,
4. Branch C summary navigation,
5. Branch B cluster overlay,
6. auth/library,
7. cloud adapters,
8. upload/sync.

This preserves the highest-value traceability loop first while keeping cluster behavior additive.

---

## Risks, Ambiguity Points, and Anti-Patterns to Avoid

### Risk 1 — Letting raw markdown become the runtime contract

#### Problem

Branch A and Branch B markdown artifacts are readable, but they are not stable runtime contracts.

#### Avoid

- parsing headings, citations, or cluster membership from markdown strings at runtime

#### Safer path

- generate normalized render JSON and make templates consume that instead

### Risk 2 — Binding service logic directly to `data/` folder structure

#### Problem

The sample data is useful but not the final runtime storage model.

#### Avoid

- hard-coding stage directory semantics into route or service logic

#### Safer path

- isolate raw sample knowledge in importer/sample-loader and packager modules

### Risk 3 — Treating every Branch B sample artifact as equally reliable

#### Problem

Some Branch B variants are empty or incomplete.

#### Avoid

- assuming cluster data is always present

#### Safer path

- make cluster packaging explicit, optional, and validation-driven

### Risk 4 — Growing frontend behavior before freezing DOM conventions

#### Problem

The JS layer will become fragile if template markup changes casually.

#### Avoid

- hidden selectors
- implicit text parsing
- one-off event binding per element

#### Safer path

- freeze explicit dataset attributes and use delegated event handling

### Risk 5 — Starting cloud integration before local artifact flow is proven

#### Problem

Cloud debugging can mask packaging and contract mistakes.

#### Avoid

- early Cloud Run, Firestore, or GCS coupling before local P0–P5 behavior works

#### Safer path

- follow the local-first validation ladder already defined in the infra guide

### Risk 6 — Over-scoping the first audio experience

#### Problem

Word-level karaoke sync, waveforms, and transcript auto-scroll are appealing but not necessary for PoC validation.

#### Avoid

- building waveform or word-synchronization infrastructure first

#### Safer path

- ship reliable piece-level seek and active-piece highlighting first

### Risk 7 — Prematurely mixing metadata and large artifacts in Firestore

#### Problem

Large render artifacts do not belong in Firestore.

#### Avoid

- storing render JSON blobs in Firestore documents

#### Safer path

- keep Firestore for metadata, preferences, and ownership; keep artifacts in file/object storage

---

## Prioritized Execution Sequence

### Recommended build sequence

1. **Freeze runtime contracts and sample variant strategy**
2. **Implement local artifact/sample adapters**
3. **Implement `ManifestPackagerService` and manifest builder CLI**
4. **Add contract tests and determinism tests for packaged outputs**
5. **Implement document loader and Branch A page**
6. **Implement piece hover, tooltip, and audio overlay flow**
7. **Implement seeded Branch C summary rendering and transcript jump flow**
8. **Implement Branch B cluster overlay and cluster panel**
9. **Add preference persistence and library polish**
10. **Add auth and tenant scoping**
11. **Swap in cloud adapters and Cloud Run deployment path**
12. **Only then add upload, orchestration, and sync features**

### Why this sequence is recommended

- It starts with the most reusable seam: packaging.
- It validates the core product interaction before platform complexity.
- It keeps Branch C ahead of Branch B in practical value.
- It leaves auth and cloud work until the renderer has real proof-of-value.

---

## Recommended Immediate Next Actions

### Immediate action set

1. **Create and freeze the runtime schemas** for:
   - `document_manifest`
   - `pieces_index`
   - `branch_a_render`
   - `audio_manifest`
   - `branch_c_render`
   - `clusters_render`

2. **Define the sample-document normalization strategy**:
   - how `sample0x_*_y` variants become local document IDs
   - how rendered outputs are stored
   - how missing optional artifacts are represented

3. **Implement the renderer packager first**:
   - consume canonical bundle + Branch A structure + usable Branch B finals
   - emit deterministic runtime manifests
   - seed Branch C until real upstream data exists

4. **Build the first end-to-end UX slice from packaged artifacts only**:
   - open document
   - render Branch A
   - hover piece
   - inspect timestamps
   - play from piece

5. **Add the summary jump path next**:
   - seeded Branch C
   - citation popover
   - jump to transcript piece

6. **Add cluster overlays after the transcript/summary/audio loops are proven**.

### Immediate non-goals

Do not make these part of the first implementation slice:

- cloud deployment hardening
- upload flows
- Google Drive sync
- heavy orchestration
- waveform rendering
- word-level karaoke sync
- complex multi-user administration

---

## Final Implementation Guidance

The project should now be treated as a **packaged-renderer system over canonical pieces**, not as a markdown viewer.

The implementation center of gravity should therefore be:

1. **renderer packaging layer**,
2. **normalized render contracts**,
3. **Branch A transcript reader**,
4. **audio seek and piece interaction flow**,
5. **Branch C grounded summary navigation**,
6. **Branch B cluster overlay**,
7. only then the account, library, upload, and sync layers.

If this order is respected, the project will maximize visible progress while minimizing architectural drift.