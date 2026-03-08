# Transcript Renderer — Infrastructure Enablement Guide

Version: 2026-03-06  
Primary target deployment: **Google Cloud Run**  
Companion documents:
- `congress_renderer_architecture_report.md`
- `transcript_renderer_implementation_plan.md`

---

## 0. Read this first

This document is the **infrastructure-only companion** to `transcript_renderer_implementation_plan.md`.

It tells the developer exactly what to enable, in which order, and how each infrastructure phase maps to the code phases.

This guide intentionally owns:
- Google Cloud project creation
- billing and cost guardrails
- region selection
- API enablement
- IAM and service accounts
- Firebase project attachment
- Firebase Auth enablement
- Firestore enablement
- GCS bucket creation
- Cloud Run service deployment
- Cloud Run Job preparation
- CI/CD enablement
- secrets and budgets
- staging/production-ish PoC setup

This guide intentionally does **not** own:
- Python application logic
- UI implementation
- manifest packaging code
- FastAPI route behavior
- JS reader behavior

Those belong in `transcript_renderer_implementation_plan.md`.

---

## 1. Final hosting decision

## 1.1 VM evaluation result

Google Compute Engine **does** expose an Always Free path:
- 1 non-preemptible `e2-micro` instance per month
- available in `us-west1`, `us-central1`, `us-east1`
- 30 GB-months of standard persistent disk
- 1 GB/month outbound transfer

That makes a VM technically possible for the PoC.

## 1.2 Why this guide still targets Cloud Run

Despite the VM free tier existing, this guide keeps **Cloud Run** as the primary target because it is better for this app’s shape:

- the web app is mostly bursty and benefits from scale-to-zero
- Cloud Run reduces OS/patching/process-management burden
- Cloud Run pairs naturally with Cloud Build and Git-based deploys
- Cloud Run Jobs provide a clean place for future async packaging/ingestion
- the app is easier to keep production-friendly while still moving quickly

## 1.3 What this means operationally

Use:
- **Cloud Run** for the FastAPI web service
- **Cloud Storage (GCS)** for artifacts and media
- **Firestore** for document catalog metadata and preferences
- **Firebase Auth** for end-user identity
- **Cloud Run Jobs** only as optional extension points for later async tasks

Do **not** use for the PoC:
- Cloud SQL
- GKE
- self-managed PostgreSQL on day one
- VM unless you intentionally opt into the appendix at the end

---

## 2. Verified free-tier and platform facts used by this guide

Verified against official Google docs on **2026-03-06**:

- Google Cloud Free Tier requires a billing account, even for always-free usage.
- Compute Engine Always Free includes one non-preemptible `e2-micro` VM per month in `us-west1`, `us-central1`, or `us-east1`, plus 30 GB-month standard persistent disk and 1 GB/month outbound transfer.
- Cloud Run has always-free monthly allocations; service requests can run up to 60 minutes.
- Cloud Run Jobs also have always-free CPU/RAM allocations and tasks can run up to 168 hours.
- Cloud Build includes 2,500 free build-minutes per billing account per month.
- Cloud Storage always-free usage is region-limited to `us-east1`, `us-west1`, `us-central1`.
- Firestore has meaningful free quotas for small PoC metadata usage.
- Firebase Auth remains a practical fit for Google sign-in and email/password.
- Firebase Storage pricing rules changed, and new/default Firebase Storage bucket workflows require Blaze.  
  Therefore, this guide uses **plain GCS** for artifact/media storage and **not Firebase Storage**.

The reference list is at the end of this guide.

---

## 3. Infrastructure bill of materials

## 3.1 Required services

| Service | Purpose | Free-tier relevance |
|---|---|---|
| Google Cloud project + billing | required foundation | mandatory even for Free Tier |
| Cloud Run | web app hosting | strong always-free fit |
| Cloud Build | source/Git builds | useful free allowance |
| Artifact Registry | container artifacts if needed | minimal storage use only |
| Cloud Storage (GCS) | audio + render artifacts | always-free in selected US regions |
| Firestore | metadata + preferences | good free quota for PoC |
| Firebase project linkage | enables Auth / frontend SDK ergonomics | needed for auth path |
| Firebase Authentication | Google + email/password auth | good fit for PoC |
| Secret Manager | service secrets if needed | small usage likely within free allowance |
| Cloud Logging / Monitoring | observability | use lightly in PoC |
| Cloud Run Jobs (optional) | future async packaging | supported, not required on day one |

## 3.2 Explicitly excluded for initial PoC

| Service | Why excluded |
|---|---|
| Cloud SQL | too easy to create recurring cost, unnecessary now |
| GKE | too much operational and billing surface |
| Firebase Storage | not needed; plain GCS is simpler and avoids bucket-plan confusion |
| Pub/Sub | defer unless async orchestration becomes necessary |
| Load balancer / CDN stack | unnecessary before traffic or custom domain pressure |
| Memorystore / Redis | not required for this UX |

---

## 4. Region policy

Use these regions unless there is a documented reason to change:

| Component | Region |
|---|---|
| Cloud Run service | `us-central1` |
| Cloud Run jobs | `us-central1` |
| GCS bucket | `us-central1` |
| Firestore | closest compatible low-complexity region; prefer same US footprint for PoC |
| Artifact Registry | `us-central1` |

Why:
- aligns with strong free-tier assumptions
- keeps Cloud Run pricing basis aligned with published free-tier examples
- keeps GCS in one of the always-free eligible US regions
- reduces surprise in cost calculations

Do not spread the PoC across multiple regions unless required.

---

## 5. Mapping: implementation phases vs infrastructure phases

This is the primary coordination table between this guide and the implementation plan.

| Infra Phase | Enables | Required by implementation phases |
|---|---|---|
| I0 | local-only work, no cloud | P0, P1, P2, large parts of P3/P4/P5 |
| I1 | GCP project, billing, APIs, CLI access | required before any cloud test |
| I2 | Firebase + Auth + Firestore foundations | required before P6 cloud auth |
| I3 | GCS buckets + IAM + service accounts | required before P7 cloud adapters |
| I4 | Cloud Run service deploy path | required before first hosted staging test |
| I5 | CI/CD + budgets + alerts + secrets | required before team-facing PoC |
| I6 | Optional Cloud Run Jobs path | only required for later async packaging/ingestion |

---

## 6. Infra phase I0 — local-first preparation

This phase intentionally avoids cloud work.

## 6.1 Purpose

Allow developers to complete:
- P0
- P1
- P2
- most of P3/P4/P5

without being blocked by cloud setup.

## 6.2 Required local tools

Install locally:
- Python 3.11+
- `gcloud` CLI
- Git
- browser with devtools
- optional: Docker only if later needed
- optional: Firebase CLI for auth/emulator convenience

## 6.3 Local environment contract

Developers should be able to run the app with:
- fake auth
- local filesystem artifact store
- local document repository
- local preference repository

This reduces early risk and keeps progress visible.

## 6.4 Validation

A developer must be able to run:

```bash
uvicorn app.main:app --reload
```

and complete all validations from implementation phases P0–P5 using sample data only.

If this is not true, do not move cloud integration earlier. Fix local seams first.

---

## 7. Infra phase I1 — create the Google Cloud foundation

## 7.1 Purpose

Create the minimal cloud foundation needed for hosted testing.

## 7.2 Preconditions

Before starting I1, the codebase should already satisfy:
- P0
- preferably P1 and P2

This reduces the chance of enabling cloud resources before the app can even boot cleanly.

## 7.3 Required steps

### 7.3.1 Create/select project

Create one dedicated PoC project.

Recommended naming:

```text
Project display name: Transcript Renderer POC
Project ID: transcript-renderer-poc-<suffix>
```

Do not reuse a noisy existing project if avoidable.

### 7.3.2 Link billing account

This is mandatory because Google Cloud Free Tier requires a billing account.

### 7.3.3 Enable APIs

Enable these APIs first:

- Cloud Run Admin API
- Cloud Build API
- Artifact Registry API
- Firestore API
- Cloud Storage API
- Secret Manager API
- IAM API
- Cloud Logging API

Add later only if needed:
- Firebase Management / Identity Toolkit related APIs are usually enabled as part of Firebase/Auth workflows
- Cloud Run Jobs uses Cloud Run Admin API
- Cloud Scheduler / Pub/Sub only if later introduced

### 7.3.4 Configure CLI

```bash
gcloud auth login
gcloud config set project PROJECT_ID
gcloud config set run/region us-central1
```

## 7.4 Cost guardrails (mandatory)

Immediately after billing is linked:
1. create a budget
2. add low thresholds such as 25%, 50%, 75%, 90%
3. route budget alerts to email

This is non-optional.  
PoC work is where accidental small charges become recurring unnoticed charges.

## 7.5 Validation

### Commands

```bash
gcloud config get-value project
gcloud services list --enabled
```

### Expected result

- correct project selected
- required APIs enabled
- billing linked
- budget configured

## 7.6 Common failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| Cloud Run deploy blocked | billing not enabled | link billing, confirm project context |
| Firestore creation unavailable | API not enabled or wrong project | re-check active project and API list |
| team member cannot enable service | missing IAM role | use Owner/Admin temporarily for bootstrap, reduce later |

---

## 8. Infra phase I2 — Firebase, Authentication, and Firestore

## 8.1 Purpose

Enable end-user identity and user-scoped metadata persistence.

## 8.2 Preconditions

Implementation:
- P0–P5 can be locally validated
- P6 auth interfaces exist, even if using fake auth

Infrastructure:
- I1 complete

## 8.3 Firebase project linkage

Attach Firebase to the same Google Cloud project.

Reason:
- one project keeps auth + firestore + run simpler for the PoC
- easier environment variable and credential management
- fewer cross-project IAM surprises

## 8.4 Enable Authentication providers

Enable at minimum:
- Google sign-in
- email/password

Do not enable phone auth unless required later.

## 8.5 Firestore creation

Create **one Firestore database** for the PoC.

Use Firestore for:
- document catalog metadata
- user ownership metadata
- reader preference data
- later job status if needed

Do not use it for:
- large branch render JSON blobs
- audio storage
- large raw pipeline outputs

## 8.6 Suggested collections

```text
users/{user_id}
documents/{document_id}
documents/{document_id}/access/{user_id}
preferences/{user_id}
```

Alternative denormalized pattern is acceptable, but keep these rules:
- document ownership query must be cheap
- preference lookup must be by user
- document metadata must not embed huge artifacts

## 8.7 Validation

### Firebase/Auth validation

- test a Google login in a dev/staging web page
- test email/password sign-up and sign-in
- verify user object is created

### Firestore validation

- create one test preference document manually or via app
- verify app can read it back

## 8.8 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| frontend login succeeds but backend sees anonymous user | backend token verification not configured | wire Firebase Admin credentials and auth dependency |
| Firestore reads fail in Cloud Run | service account missing Firestore access | update IAM on runtime service account |
| auth works locally only | wrong web app config or redirect domain mismatch | verify Firebase web config and authorized domains |

---

## 9. Infra phase I3 — GCS buckets, IAM, and service accounts

## 9.1 Purpose

Create durable storage for:
- imported artifacts
- render manifests
- audio media

## 9.2 Why plain GCS, not Firebase Storage

Use **plain Google Cloud Storage** for this app because:
- the backend is already server-based
- GCS is enough for the use case
- you avoid Firebase Storage plan/bucket behavior confusion
- signed URLs or proxy streaming are straightforward

## 9.3 Bucket plan

Use one bucket for the PoC unless there is a security reason to split:

```text
gs://<project-id>-renderer-poc
```

Namespace objects by tenant/document:

```text
tenants/<tenant_id>/documents/<document_id>/source/...
tenants/<tenant_id>/documents/<document_id>/render/...
tenants/<tenant_id>/documents/<document_id>/media/...
```

## 9.4 Bucket region

Use `us-central1`.

This keeps the bucket inside one of the always-free-eligible GCS regions.

## 9.5 Service account strategy

Create at least one explicit runtime service account for Cloud Run:

```text
renderer-runtime@PROJECT_ID.iam.gserviceaccount.com
```

Grant only what is needed:
- read/write to the bucket
- Firestore access
- Secret access if used

Avoid running the app with an over-privileged default account if possible.

## 9.6 Validation

### CLI checks

```bash
gcloud storage buckets list
gcloud iam service-accounts list
```

### Functional checks

- upload one small test file
- download/read it from a local script or staging app
- generate one signed URL if using that pattern

## 9.7 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| app can read local files but not GCS | wrong adapter config or missing credentials | verify env vars and runtime service account |
| signed URLs fail | service account permissions or wrong path | verify bucket/object path and signing method |
| bucket charges appear unexpectedly | region or egress assumptions wrong | confirm region and keep browser/media access patterns tight |

---

## 10. Infra phase I4 — deploy the Cloud Run web service

## 10.1 Purpose

Host the FastAPI application as the primary PoC environment.

## 10.2 Preconditions

Implementation:
- P0 done
- ideally P1–P3 done before first real hosted demo
- P7 cloud adapters ready for at least one document path if cloud-backed test is intended

Infrastructure:
- I1–I3 done

## 10.3 Deployment mode

Primary recommendation:
- use **Cloud Run deploy from source / Git-based path** for the PoC

Reasons:
- simplest developer flow
- no Dockerfile required at the beginning
- easy link with GitHub
- build/deploy path already supported cleanly

## 10.4 Environment variables

At minimum, configure:

```text
APP_APP_ENV=staging
APP_ARTIFACT_STORE_BACKEND=gcs
APP_DOCUMENT_REPO_BACKEND=firestore
APP_PREFERENCES_REPO_BACKEND=firestore
APP_AUTH_BACKEND=firebase
APP_GCS_BUCKET=<bucket-name>
APP_FIRESTORE_DATABASE=(default or chosen name)
APP_FIREBASE_PROJECT_ID=<project-id>
```

Exact variable names should match the code implementation plan.

## 10.5 Runtime service account

Attach the explicit runtime service account created in I3.

Do not let the service run with broader credentials than necessary.

## 10.6 Public vs private access

For the PoC, the web frontend service can be public.

App-layer auth still protects document access.

Do not make internal admin or future job callbacks public unless needed.

## 10.7 Resource shape

Start with a conservative config:
- 1 CPU
- modest memory
- min instances = 0
- max instances small
- timeout adequate for UI/API requests, but not abused for heavy processing

Heavy long-running work belongs later in Cloud Run Jobs, not in user-facing web requests.

## 10.8 Validation

### Functional hosted checks

- homepage loads
- login works
- one document loads
- piece hover works
- audio resolves
- summary jump works

### Operational checks

- logs visible in Cloud Logging
- service revision history visible
- rollback path understood

## 10.9 Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| deploy succeeds but service 500s | app startup mismatch / env vars missing | inspect revision logs |
| service cannot access Firestore | runtime SA missing permissions | adjust IAM |
| service cannot serve static assets | buildpack entrypoint or template/static path issue | verify root `main.py`, `Procfile`, static mount |
| branch reader loads but media fails | bucket path or signed URL issue | inspect app logs and browser network panel |

---

## 11. Infra phase I5 — CI/CD, secrets, observability, and budgets

## 11.1 Purpose

Make the PoC repeatable for developer handoff and demo use.

## 11.2 Git-based deployment

Connect GitHub to Cloud Run or use Cloud Build trigger flow.

Recommended behavior:
- deploy from `main` or `staging` branch to staging service
- optional manual approval before production-like service
- commit to repo is the deployment unit

## 11.3 Secrets

Use Secret Manager for anything that should not live directly in environment config.

Candidates:
- service account JSON only if a library absolutely requires it
- API keys for future external services
- signing secrets if introduced later

Do not overuse secrets for values that are not secret.

## 11.4 Logging and observability

Enable:
- Cloud Logging
- error visibility in revision logs
- request correlation if simple to add
- optionally one uptime check later

Do not prematurely build a full observability stack.

## 11.5 Budgets and alerts

Required:
- billing budget
- threshold alerts
- service owners subscribed

Recommended:
- monthly check of billing report
- verify no idle paid resources appear

## 11.6 Validation

- push a small code change
- confirm automatic build/deploy triggers
- confirm logs show the new revision
- confirm budget alerts are configured

---

## 12. Infra phase I6 — optional Cloud Run Jobs path

## 12.1 Purpose

Prepare for later async tasks without distorting the web service.

Potential later uses:
- package manifests after upload
- re-index documents
- background validation
- future upload processing orchestration

## 12.2 Do not enable this early unless needed

The current application can be demonstrated without Cloud Run Jobs.

Only enable once:
- the web service path is stable
- local packaging flow is proven
- the team is ready to separate interactive vs batch work

## 12.3 Validation

Deploy one no-op or simple diagnostic job first.

Example idea:
- read one test document from GCS
- write a small report JSON back to GCS

This validates:
- job permissions
- bucket permissions
- runtime environment
- logging

---

## 13. Minimum IAM model for the PoC

Use principle of least privilege, but do not overcomplicate.

## 13.1 Human roles

Bootstrap owner/admin temporarily:
- project creation
- billing linkage
- API enablement
- Firebase setup

Then narrow where practical.

## 13.2 Runtime identity

Cloud Run runtime service account should have only:
- Storage Object access to the PoC bucket
- Firestore access
- Secret access only if needed

## 13.3 CI/CD identity

Build/deploy identity needs:
- Cloud Run deploy permissions
- Artifact Registry permissions
- service account user permission for runtime account if attaching it

Do not reuse runtime credentials for CI.

---

## 14. Local-to-cloud test ladder

This is the recommended order of confidence building.

### Step 1 — local only
Required before cloud:
- P0–P2 passing locally

### Step 2 — local rich UX
Recommended before cloud:
- P3–P5 passing locally

### Step 3 — cloud shell deployment
Deploy app to Cloud Run using fake auth and maybe local-like seeded cloud data

### Step 4 — cloud auth + storage
Enable real Firebase auth and GCS-backed artifacts

### Step 5 — user-scoped demo
Run full demo flow as a real user

Do not jump from broken local straight into cloud debugging. That is slow and misleading.

---

## 15. What must be finished before enabling each infrastructure piece

| Infrastructure piece | Do not enable before this code exists |
|---|---|
| Firestore for real app data | repository interfaces frozen, P6 auth/prefs contract exists |
| GCS artifact path | artifact store contract frozen, packager output paths defined |
| Cloud Run staging deploy | app boots cleanly, P0 complete |
| Public demo URL | at least P3 complete and basic auth story understood |
| GitHub auto-deploy | one manual deploy already succeeded |
| Cloud Run Jobs | packager logic already works locally |

---

## 16. What infrastructure must be ready before each implementation phase can be cloud-tested

| Implementation phase | Infra needed for local test | Infra needed for cloud test |
|---|---|---|
| P0 | none | I1 + I4 |
| P1 | none | I1 + I4 |
| P2 | none | I1 + I3 + I4 only if packaging is exercised in cloud |
| P3 | none | I1 + I3 + I4 |
| P4 | none | I1 + I3 + I4 |
| P5 | none | I1 + I3 + I4 |
| P6 | fake auth only | I1 + I2 + I4 |
| P7 | optional | I1 + I2 + I3 + I4 |

---

## 17. Recommended exact enablement order

1. Complete local P0–P2.
2. Enable I1 foundation.
3. Perform first Cloud Run deploy with fake auth.
4. Complete local P3–P5 if not already done.
5. Enable I3 GCS and validate cloud-backed artifacts.
6. Enable I2 Firebase Auth + Firestore and complete P6.
7. Enable I5 CI/CD and budgets.
8. Enable I6 only when async work is truly needed.

This order minimizes the chance that cloud issues mask application issues.

---

## 18. Appendix A — If you deliberately choose the GCE e2-micro VM path

This appendix is only for the case where you intentionally prefer VM hosting despite the main recommendation remaining Cloud Run.

## 18.1 When a VM is reasonable

Choose the VM path only if:
- you strongly prefer a single long-lived host
- you want full OS-level control
- you accept Linux patching and process supervision work
- the app will stay tiny and low-traffic
- you want to avoid Cloud Run request/runtime semantics

## 18.2 VM shape

Use the always-free eligible shape only:
- `e2-micro`
- one of `us-west1`, `us-central1`, `us-east1`
- standard persistent disk within the free allowance

## 18.3 App serving on VM

Recommended:
- `gunicorn` + `uvicorn_worker`
- reverse proxy via Nginx or Caddy
- systemd service for app process
- use GCS/Firestore/Firebase the same way as the Cloud Run plan

## 18.4 Why VM is still second choice

Main drawbacks versus Cloud Run:
- you manage OS lifecycle
- you manage process restarts
- scale-to-zero is gone
- deploy/rollback is more manual
- easier to create hidden ops work during the PoC

---

## 19. Reference list (official sources)

The following references informed the decisions in this guide and were verified on 2026-03-06.

### Google Cloud Free Tier / Compute Engine
1. Google Cloud Free Program — Free Tier features  
   https://docs.cloud.google.com/free/docs/free-cloud-features

### Cloud Run
2. Cloud Run pricing  
   https://cloud.google.com/run/pricing
3. Cloud Run request timeout  
   https://docs.cloud.google.com/run/docs/configuring/request-timeout
4. Cloud Run Jobs task timeout  
   https://docs.cloud.google.com/run/docs/configuring/task-timeout
5. Deploy services from source code / GitHub continuous deployment  
   https://docs.cloud.google.com/run/docs/deploying-source-code
6. Cloud Run quickstart deploy container  
   https://docs.cloud.google.com/run/docs/quickstarts/deploy-container
7. Cloud Run quickstart deploy continuously  
   https://docs.cloud.google.com/run/docs/quickstarts/deploy-continuously

### Cloud Build
8. Cloud Build pricing  
   https://cloud.google.com/build/pricing

### Firebase / Firestore / Authentication / Storage pricing changes
9. Firebase pricing  
   https://firebase.google.com/pricing
10. Firebase Authentication docs  
    https://firebase.google.com/docs/auth
11. Firebase Authentication limits  
    https://firebase.google.com/docs/auth/limits
12. Firestore quotas / pricing  
    https://firebase.google.com/docs/firestore/quotas
13. Firestore pricing details  
    https://firebase.google.com/docs/firestore/pricing
14. Firebase FAQ (Spark vs Blaze, Google Cloud features availability)  
    https://firebase.google.com/support/faq
15. Firebase Storage pricing-plan change FAQ  
    https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024

---

## 20. Handoff summary

A developer receiving this guide should be able to:
- create the minimal correct Google Cloud foundation
- avoid the major free-tier traps
- sequence infrastructure in parallel with implementation
- know exactly which infra is needed for which code phase
- keep the PoC cheap, simple, and reversible
