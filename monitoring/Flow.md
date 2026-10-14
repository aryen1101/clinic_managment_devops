# Flow.md: Build the Clinic Management DevOps Project from Scratch

This guide explains **how to build this project yourself, one file at a time, in the right order**. After each step it gives the command that proves the step works, the Git commit to make, and the screenshot to take for the submission.

All the finished code is already in this folder, so you can use it in two ways:
- **Learn and rebuild:** create an empty folder and write each file in the order below, using the files here as your reference. This is the best way to be able to explain everything in the viva.
- **Use as-is:** follow the same order to *read and understand* each file, run every verification command, and take the screenshots.

> The instructor allows AI-written code, *as long as you understand it*. Each step below says what the file does and why it exists. Read those notes.

---

## 0. The big picture

**App:** *CareDesk*, a clinic management system with three related tables:

```text
patients 1 ──── * appointments * ──── 1 doctors
```

**Order of work:** build the app first, then wrap the DevOps layers around it from the inside out:

```text
 Phase 1  Git repo + .gitignore                     (M3)
 Phase 2  Backend API + database migration          (M1)
 Phase 3  Tests                                     (M2)
 Phase 4  Frontend UI                               (M1)
 Phase 5  Docker + Docker Compose                   (M4)
 Phase 6  GitHub Actions CI/CD + GHCR               (M5)
 Phase 7  DevSecOps scanners                        (M6)
 Phase 8  Kubernetes manifests (k8s/)               (M8)
 Phase 9  Helm chart + Minikube + Ingress + HPA     (M8)
 Phase 10 Prometheus + Grafana                      (M9)
 Phase 11 GitOps with Argo CD                       (Assignment extra)
 Phase 12 Terraform (AWS VPC + EKS)                 (M7)
 Phase 13 Troubleshooting challenge                 (Assignment)
 Phase 14 README, screenshots, PPT, video, demo     (M10)
```

**Why this order?** Every layer depends on the one before it. You can't containerize an app that doesn't work, you can't run CI without tests, and you can't deploy to Kubernetes without images in a registry.

---

## 1. Prerequisites (Windows)

| Tool | Check | Install |
|---|---|---|
| Git | `git --version` | git-scm.com |
| Python 3.12+ | `python --version` | python.org |
| Node.js 22 | `node --version` | nodejs.org |
| Docker Desktop | `docker version` | docker.com |
| kubectl | `kubectl version --client` | included with Docker Desktop |
| Minikube or kind | `minikube version` | `winget install Kubernetes.minikube` |
| Helm | `helm version` | `winget install Helm.Helm` |
| Terraform | `terraform version` | `winget install Hashicorp.Terraform` |
| AWS CLI (optional) | `aws --version` | aws.amazon.com/cli |
| A GitHub account | | |

Use **Git Bash** for the commands in this guide (the `.sh` scripts need it).

---

## Phase 1: Git repository (M3, 5 pts)

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `.gitignore` | **First file, always.** Keeps `.env`, `__pycache__/`, `.venv/`, `node_modules/`, `*.tfstate`, `*.tfvars` and kubeconfigs out of Git. Grading checks for the first four. |

### Do
```bash
mkdir clinic-management && cd clinic-management
git init
# create .gitignore
git add .gitignore
git commit -m "chore: add gitignore for python, node, terraform and secrets"
```
Create an empty **public** repo on GitHub named `clinic-management`, then:
```bash
git branch -M main
git remote add origin https://github.com/<you>/clinic-management.git
git push -u origin main
```

### Rules for the rest of the project
- Commit at the end of **every step** in this guide. That gives 20+ commits, and grading needs at least 10.
- Use meaningful messages (`feat(api): ...`, `test: ...`, `ci: ...`), never "update" or "fix".

---

## Phase 2: Backend API + database (M1, part of 10 pts)

Write the backend **bottom-up**: settings, then the database connection, then tables, then validation, then endpoints, then the app.

### Files, in order
| # | File | What it does / why |
|---|---|---|
| 1 | `backend/requirements.txt` | Runtime libraries with **pinned versions**: FastAPI, Uvicorn, SQLAlchemy, psycopg, Pydantic, Alembic, Prometheus instrumentator. Pinning makes builds reproducible. |
| 2 | `backend/app/__init__.py` | Empty. Makes `app` a Python package. |
| 3 | `backend/app/config.py` | Reads settings from environment variables. Supports one `DATABASE_URL` (Compose, tests) **or** separate `DB_HOST/DB_USER/DB_PASSWORD...` (Kubernetes: ConfigMap + Secret). |
| 4 | `backend/app/db.py` | Creates the SQLAlchemy `engine` and `SessionLocal`, the `Base` class for models, and `get_db()`, which gives every request its own DB session. |
| 5 | `backend/app/models.py` | The 3 tables as Python classes: `Doctor`, `Patient`, `Appointment`, with foreign keys and cascade delete. |
| 6 | `backend/app/schemas.py` | Pydantic models: what the API **accepts** (`*Create`, `*Update`) and **returns** (`*Out`). Validation lives here: phone/email format, gender enum, date of birth not in the future. |
| 7 | `backend/app/routers/__init__.py` | Empty package file. |
| 8 | `backend/app/routers/common.py` | `get_or_404()` helper, reused by every router. |
| 9 | `backend/app/routers/patients.py` | Patients CRUD + search + visit history. |
| 10 | `backend/app/routers/doctors.py` | Doctors CRUD + filters + unique email (409). |
| 11 | `backend/app/routers/appointments.py` | Appointments CRUD + **business rules**: no double-booking (409), doctor must be available (400). Also defines the custom Prometheus counter. |
| 12 | `backend/app/routers/dashboard.py` | `GET /api/stats` for the dashboard cards. |
| 13 | `backend/app/main.py` | Creates the FastAPI app: CORS, `/metrics`, request-logging middleware, `/`, `/health` (liveness, no DB), `/ready` (readiness, checks DB), and includes the 4 routers. |
| 14 | `backend/alembic.ini` | Alembic config. `prepend_sys_path = .` is required, otherwise `env.py` can't import `app`. |
| 15 | `backend/alembic/script.py.mako` | Template Alembic uses for new migration files. |
| 16 | `backend/alembic/env.py` | Connects Alembic to our models and DB URL. Takes a **Postgres advisory lock**, so two pods starting together don't run migrations at the same time. |
| 17 | `backend/alembic/versions/0001_create_clinic_tables.py` | The migration that creates the 3 tables + indexes. **Graded:** "at least one table managed by Alembic". |
| 18 | `backend/app/seed.py` | Inserts demo doctors, patients and appointments, so the UI isn't empty in screenshots. |
| 19 | `backend/app/wait_for_db.py` | Retries the DB connection for up to 60s before migrations run. Prevents CrashLoopBackOff when the backend starts before Postgres. |
| 20 | `backend/.env.example` | Example env file for local runs. The real `.env` is git-ignored. |

### Verify
```bash
# a throw-away Postgres for development
docker run -d --name clinic-db -e POSTGRES_DB=clinic -e POSTGRES_USER=clinic -e POSTGRES_PASSWORD=clinic -p 5432:5432 postgres:17-alpine

cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head              # → "Running upgrade -> 0001_create_clinic_tables"
python -m app.seed                # → "Seed complete: 4 doctors, 4 patients, 5 appointments"
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs and try every endpoint (**Try it out → Execute**). Then check the business rules: booking the same doctor/date/time twice must return **409**.

### Commits
```text
feat(api): add settings, database session and ORM models
feat(api): add pydantic schemas with validation
feat(api): add patients, doctors and appointments CRUD routers
feat(api): add health, readiness and prometheus metrics endpoints
feat(db): add alembic migration for clinic tables
feat(api): add demo seed data and wait-for-db startup check
```

### Screenshots
- `m1-swagger.png`: `/docs` showing all endpoints
- `m1-health.png`, `m1-ready.png`: JSON from `/health` and `/ready`
- `m1-db-table.png`: `docker exec -it clinic-db psql -U clinic -d clinic -c '\dt'` and `-c 'select * from doctors;'`

---

## Phase 3: Tests (M2, 10 pts)

Graded: pytest passes · **≥5 tests over ≥3 endpoints** · **test DB, not production** · `pytest.ini`/`conftest.py` present. This project has **24 tests**.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `backend/requirements-dev.txt` | Dev-only tools: pytest, pytest-cov, httpx, ruff, bandit, pip-audit. Kept out of the Docker image. |
| 2 | `backend/pytest.ini` | Tells pytest where tests are and adds `.` to the import path. |
| 3 | `backend/ruff.toml` | Linter rules (code quality). |
| 4 | `backend/tests/conftest.py` | **Key file.** Sets `DATABASE_URL` to a temporary **SQLite** file *before* importing the app, recreates empty tables for every test, and provides `client`, `doctor` and `patient` fixtures. |
| 5 | `backend/tests/test_system.py` | `/`, `/health`, `/ready`, `/metrics` |
| 6 | `backend/tests/test_patients.py` | create, validation (422), list/search, 404, update, cascade delete |
| 7 | `backend/tests/test_doctors.py` | create, duplicate email (409), filter, update/delete |
| 8 | `backend/tests/test_appointments.py` | book, unknown patient (404), double-booking (409), re-book cancelled slot, unavailable doctor (400), status update, filters, history, delete, stats |

### Verify
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v                  # 24 passed
ruff check .               # All checks passed!
```

### Commit / screenshot
```text
test(api): add conftest with isolated sqlite db and 24 API tests
```
- `m2-pytest.png`: terminal showing `pytest -v` with all tests green

---

## Phase 4: Frontend (M1, rest of the 10 pts)

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `frontend/package.json` | Dependencies (React, Vite) with exact versions. Run `npm install` once to create **`package-lock.json`** and commit it (CI uses `npm ci`). |
| 2 | `frontend/vite.config.js` | Dev server on :5173 that **proxies `/api` to :8000**, so the browser only ever uses relative URLs. |
| 3 | `frontend/index.html` | HTML shell with `<div id="root">`. |
| 4 | `frontend/src/main.jsx` | Mounts `<App/>` into the page. |
| 5 | `frontend/src/api.js` | One place for all HTTP calls (`api.list/create/update/remove`). Turns FastAPI error messages into readable text. |
| 6 | `frontend/src/utils.js` | `useLoader` hook (loading/error/data), date/time/age formatting. |
| 7 | `frontend/src/components/Sidebar.jsx` | Navigation. |
| 8 | `frontend/src/components/Modal.jsx` | Reusable dialog (closes on Esc or a backdrop click). |
| 9 | `frontend/src/components/Common.jsx` | `PageHeader`, `StatCard`, `StatusBadge`, `ErrorBanner`, `Empty`. |
| 10 | `frontend/src/pages/Dashboard.jsx` | KPI cards, today's schedule, status bars, live health of the API and DB. |
| 11 | `frontend/src/pages/Patients.jsx` | Table + search + create/edit/delete + visit-history modal. |
| 12 | `frontend/src/pages/Doctors.jsx` | Card grid + availability switch + create/edit/delete. |
| 13 | `frontend/src/pages/Appointments.jsx` | Filters, table, complete/cancel buttons, booking form. |
| 14 | `frontend/src/App.jsx` | Layout, page switching (`#hash` URLs), toast notifications. |
| 15 | `frontend/src/styles.css` | Design tokens + responsive breakpoints (1100px, 860px, 560px). |

### Verify
```bash
# backend from Phase 2 still running on :8000
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # must succeed; CI runs this
```
Click through everything: register a patient, add a doctor, book an appointment, complete it, try to double-book, delete. Then press **F12**, open the device toolbar and pick a phone size to check the responsive layout.

### Commits / screenshots
```text
feat(ui): add react app shell, api client and shared components
feat(ui): add dashboard, patients, doctors and appointments pages
style(ui): responsive layout for tablet and mobile
```
- `m1-ui-dashboard.png`, `m1-ui-create.png` (a booking modal), `m1-ui-mobile.png` (phone view)

---

## Phase 5: Docker + Docker Compose (M4, 10 pts)

Graded: backend Dockerfile builds · **frontend multi-stage** · **both non-root** · `docker compose up --build` starts all 3.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `backend/.dockerignore` | Keeps `.venv`, tests, caches and `.env` out of the image. |
| 2 | `backend/Dockerfile` | `python:3.13-slim` → install requirements (cached layer) → **remove pip** (Trivy finding) → user **uid 10001** → copy code → `HEALTHCHECK` → start command: wait for DB → `alembic upgrade head` → uvicorn. |
| 3 | `frontend/nginx.conf.template` | nginx serves the React build, falls back to `index.html`, and **proxies `/api` to `${BACKEND_URL}`**. It's a template, so the same image works in Compose (`http://backend:8000`) and Kubernetes (`http://clinic-backend:8000`). |
| 4 | `frontend/.dockerignore` | Keeps `node_modules` and `dist` out of the build context. |
| 5 | `frontend/Dockerfile` | **Stage 1** `node:22-alpine`: `npm ci && npm run build`. **Stage 2** `nginx-unprivileged`: `apk upgrade` (CVE fixes), copy `dist/` + the template, runs as **uid 101** on port **8080**. |
| 6 | `docker-compose.yml` | 3 services · named volume for Postgres data · **healthchecks**, with the backend waiting for a *healthy* DB and the frontend for a *healthy* backend · private bridge network · Postgres not exposed to the host · ports configurable via `FRONTEND_PORT` / `BACKEND_PORT`. |

### Verify
```bash
docker compose up --build              # leave running; screenshot this terminal
# new terminal:
docker compose ps                      # 3 services, backend/postgres "healthy"
docker compose exec backend whoami     # appuser   ← non-root
docker compose exec frontend whoami    # nginx     ← non-root
docker compose exec backend python -m app.seed
./scripts/smoke-test.sh                # all ✔
```
Open http://localhost:3000.

> Port 3000/8000 busy (e.g. TaskBoard is still running)? `FRONTEND_PORT=3100 BACKEND_PORT=8100 docker compose up --build`, or stop the other stack.

### Commits / screenshots
```text
build(docker): add non-root backend image with healthcheck
build(docker): add multi-stage non-root frontend image with nginx template
build(compose): add full stack with healthchecks, volume and network
```
- `m4-compose-up.png`, `m4-compose-ps.png`, `m4-nonroot.png`, `m4-browser.png`

---

## Phase 6: CI/CD with GitHub Actions (M5, 15 pts)

Graded: workflow exists · runs on push to `main` · **pytest fails the build** · frontend built · both images built · **pushed to GHCR** · **tagged with the commit SHA**.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `.github/workflows/ci-cd.yml` | 5 jobs: **test** → **security** → **build-scan-push** → **deploy-kind** → **gitops-update** (details in README §9). |

(The `security` job is explained in Phase 7, `deploy-kind` needs `k8s/` from Phase 8, and `gitops-update` needs `helm/clinic/values-gitops.yaml` from Phase 9. Write the whole workflow now, or add those jobs as you reach those phases.)

### GitHub settings (one-time)
1. **Settings → Actions → General → Workflow permissions → "Read and write permissions"** → Save. The `gitops-update` job needs this to push.
2. Nothing else. GHCR login uses the built-in `GITHUB_TOKEN`, so no secrets are needed.

### Verify
```bash
git add .
git commit -m "ci: add pipeline with tests, image build, ghcr push and kind deploy"
git push
```
GitHub → **Actions** tab, then watch every job go green.
After the first successful run: your GitHub **profile → Packages** shows `clinic-backend` and `clinic-frontend`, each with a 40-character SHA tag.
**Make both packages public** (package → *Package settings* → *Change visibility*), so Minikube and Argo CD can pull them without credentials.

**Prove the quality gate (great for marks and the demo):**
```bash
# break a test on purpose, e.g. change assert response.status_code == 409 to 200 in test_appointments.py
git commit -am "test: demonstrate failing quality gate" && git push    # pipeline goes RED, nothing is pushed
git revert HEAD --no-edit && git push                                  # back to green
```

### Screenshots
- `m5-pipeline-green.png` (and paste the **run URL** into README §9)
- `m5-pipeline-red-gate.png` (bonus)
- `m5-ghcr-packages.png`: package page showing SHA tags
- `m5-kind-deploy-log.png`: the deploy-kind job log with pods Running and "Smoke test passed"

---

## Phase 7: DevSecOps (M6, 5 pts + assignment extras)

Graded: Trivy on **both** images in CI · **fails on HIGH/CRITICAL** · you can explain one CVE (or a clean result).

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `security/README.md` | Explains each layer: SAST (Bandit), SCA (pip-audit, npm audit), secrets (Gitleaks), IaC (Trivy config), containers (Trivy image), plus **the real CVEs found and how they were fixed**. |
| 2 | `security/.trivyignore` | Where you'd accept a CVE, always with a reason. Currently empty. |
| (3) | `security` job + Trivy steps in `ci-cd.yml` | Already written in Phase 6. |

### Run the scanners locally (optional, but it's how the CVEs were found)
```bash
cd backend && bandit -r app -ll && pip-audit -r requirements.txt && cd ..
cd frontend && npm audit --audit-level=high && cd ..
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL --ignore-unfixed clinic-frontend:local
```

### The CVE story for the viva (it really happened)
The first Trivy scan **failed both images** with 47 HIGH CVEs:
- **Frontend:** 43 in Alpine packages of the nginx base image (e.g. **CVE-2026-33630, c-ares** use-after-free). Fix: `apk upgrade --no-cache`.
- **Backend:** 4 in libraries vendored inside **pip** (e.g. **CVE-2026-97687, urllib3**). Fix: `pip uninstall -y pip`, since it isn't needed at runtime.
After the fixes: **0 HIGH/CRITICAL**, and the gate passes.

### Commit / screenshots
```text
ci(security): add bandit, pip-audit, npm audit, gitleaks and trivy gates
fix(docker): patch base image CVEs found by trivy
```
- `m6-trivy-backend.png`, `m6-trivy-frontend.png` (from the pipeline log), `m6-security-job.png`
- Copy the 2–3 sentence explanation from README §10.

---

## Phase 8: Kubernetes manifests, `k8s/` (part of M8)

The instructor's approach: **plain manifests for CI on a kind cluster**, and **Helm for the "real" deployment**.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `k8s/namespace.yaml` | `clinic` namespace. **Graded:** "k8s/namespace.yaml exists and applies cleanly". |
| 2 | `k8s/config.yaml` | **ConfigMap** (APP_ENV, LOG_LEVEL, DB_HOST, DB_PORT, DB_NAME) + **Secret** (DB_USER, DB_PASSWORD, demo values for CI only). |
| 3 | `k8s/postgres.yaml` | Postgres Deployment (emptyDir: CI data is throw-away) + Service + `pg_isready` probe. |
| 4 | `k8s/backend.yaml` | Backend Deployment (2 replicas, envFrom ConfigMap, Secret refs, startup/liveness/readiness probes, resources, non-root, read-only root FS) + ClusterIP Service. Image `ghcr.io/IMAGE_OWNER/clinic-backend:IMAGE_TAG`. CI replaces the placeholders with `sed`. |
| 5 | `k8s/frontend.yaml` | Frontend Deployment (2 replicas, `BACKEND_URL=http://clinic-backend:8000`) + Service (80 → 8080). |

### Verify locally with kind (optional; CI does this on every push)
```bash
kind create cluster --name clinic-ci
docker compose build
docker tag clinic-backend:local ghcr.io/test/clinic-backend:dev
docker tag clinic-frontend:local ghcr.io/test/clinic-frontend:dev
kind load docker-image ghcr.io/test/clinic-backend:dev ghcr.io/test/clinic-frontend:dev --name clinic-ci
mkdir -p /tmp/k8s && cp k8s/*.yaml /tmp/k8s/ && sed -i "s|IMAGE_OWNER|test|g; s|IMAGE_TAG|dev|g" /tmp/k8s/*.yaml
kubectl apply -f /tmp/k8s/namespace.yaml && kubectl apply -f /tmp/k8s/
kubectl get pods -n clinic -w        # all Running, 0 restarts
kind delete cluster --name clinic-ci
```

### Commit
```text
deploy(k8s): add namespace, configmap, secret and app manifests for CI
```

---

## Phase 9: Helm + Minikube + Ingress + HPA (M8, 15 pts)

Graded: Helm chart · `helm upgrade --install` works · **≥2 replicas each** · ClusterIP Services · **Ingress `/` → frontend, `/api` → backend** · all pods Running.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `helm/clinic/Chart.yaml` | Chart name and version. |
| 2 | `helm/clinic/values.yaml` | All settings with defaults: images (tag **required**, never `latest`), replicas, resources, Postgres, Ingress, HPA, monitoring toggles. |
| 3 | `helm/clinic/values-dev.yaml` | Minikube: local images `clinic-*:local`, `pullPolicy: Never`. |
| 4 | `helm/clinic/values-prod.yaml` | EKS: `existingSecret`, gp2 storage, bigger HPA. |
| 5 | `helm/clinic/values-gitops.yaml` | Image tags written by CI for Argo CD (Phase 11). |
| 6 | `templates/_helpers.tpl` | Name helpers (`clinic-backend`...), common labels, the image helper that **fails if no tag is given**. |
| 7 | `templates/configmap.yaml` | **ConfigMap**. |
| 8 | `templates/secret.yaml` | **Secret** (skipped when `existingSecret` is set). |
| 9 | `templates/postgres.yaml` | **StatefulSet + PVC** (storage that survives restarts) + Service. |
| 10 | `templates/backend.yaml` | Deployment + Service. `checksum/config` annotations restart pods when config changes. |
| 11 | `templates/frontend.yaml` | Deployment + Service. |
| 12 | `templates/ingress.yaml` | `/api`, `/docs`, `/openapi.json`, `/health`, `/ready` → backend, `/` → frontend. |
| 13 | `templates/hpa.yaml` | HPA for backend (2–6 @ 70% CPU) and frontend (2–4 @ 80%). |
| 14 | `templates/monitoring.yaml` | ServiceMonitor, PrometheusRule (3 alerts), Grafana dashboard ConfigMap. Rendered only if the Prometheus CRDs exist. |
| 15 | `dashboards/clinic-dashboard.json` | The Grafana dashboard (11 panels). |
| 16 | `templates/NOTES.txt` | Instructions printed after `helm install`. |

### Verify
```bash
helm lint helm/clinic -f helm/clinic/values-dev.yaml

minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server            # without it the HPA shows <unknown>

docker compose build
minikube image load clinic-backend:local
minikube image load clinic-frontend:local

kubectl apply -f k8s/namespace.yaml
helm upgrade --install clinic ./helm/clinic -n clinic -f helm/clinic/values-dev.yaml --wait
kubectl exec -n clinic deploy/clinic-backend -- python -m app.seed

kubectl get pods -n clinic          # 2 backend + 2 frontend + postgres-0, all Running
kubectl get svc -n clinic
kubectl get ingress,hpa,pvc,configmap,secret -n clinic
helm list -n clinic
```
(Everything above is also in `./scripts/minikube-up.sh`.)

Using the GHCR images instead of local ones:
`helm upgrade --install clinic ./helm/clinic -n clinic --set backend.image=ghcr.io/<you>/clinic-backend --set frontend.image=ghcr.io/<you>/clinic-frontend --set backend.tag=<sha> --set frontend.tag=<sha>`

**Ingress in the browser:**
1. Open Notepad **as Administrator** → `C:\Windows\System32\drivers\etc\hosts` → add `127.0.0.1 clinic.local`
2. In a separate **admin** terminal: `minikube tunnel` (keep it open)
3. Browse to **http://clinic.local** and **http://clinic.local/docs**

**HPA demo:**
```bash
kubectl get hpa -n clinic -w             # terminal 1
./scripts/load-test.sh                   # terminal 2 → backend scales 2 → up to 6
```

**Helm lifecycle (good viva material):**
```bash
helm upgrade clinic ./helm/clinic -n clinic -f helm/clinic/values-dev.yaml --set config.logLevel=INFO
helm history clinic -n clinic
helm rollback clinic 1 -n clinic
```

### Commits / screenshots
```text
deploy(helm): add clinic chart with configmap, secret, statefulset, ingress and hpa
```
- `m8-namespace.png`, `m8-helm-install.png`, `m8-get-pods.png`, `m8-get-svc.png`, `m8-helm-list.png`
- `m8-ingress.png`: browser at `http://clinic.local`
- `m8-hpa.png`: replicas going up under load
- `m8-helm-history.png`: upgrade + rollback (bonus)

---

## Phase 10: Monitoring with Prometheus + Grafana (M9, 10 pts)

Graded: `/metrics` works · Prometheus scraping the app (target **UP**) · Grafana reachable · **a panel with live app metrics**.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `monitoring/prometheus-values.yaml` | kube-prometheus-stack values: find ServiceMonitors in **all namespaces**, Grafana password, dashboard sidecar searching all namespaces, disable control-plane scrapes that minikube doesn't expose. |
| 2 | `monitoring/README.md` | Install / access / PromQL / logs cheat sheet. |
| (3) | `helm/clinic/templates/monitoring.yaml` + `dashboards/clinic-dashboard.json` | Already written in Phase 9. |

### Verify
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml --wait
helm upgrade clinic ./helm/clinic -n clinic --reuse-values      # now creates ServiceMonitor + alerts
kubectl get servicemonitor,prometheusrule -n clinic

kubectl -n clinic port-forward svc/clinic-backend 8000:8000 &
curl http://localhost:8000/metrics | head -30                   # screenshot

kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
#  http://localhost:9090 → Status → Targets → serviceMonitor/clinic/clinic-backend/0 = UP (2/2)

kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
#  http://localhost:3001  admin / clinic-admin → Dashboards → "CareDesk Clinic - Application Overview"
```
Run `./scripts/load-test.sh` and book a few appointments in the UI, so every panel has data. Prometheus may take about 30s to pick up a new ServiceMonitor.

### Commit / screenshots
```text
feat(monitoring): add kube-prometheus-stack values, alerts and grafana dashboard
```
- `m9-metrics-curl.png`, `m9-prom-targets.png`, `m9-grafana-dashboard.png`

---

## Phase 11: GitOps with Argo CD (assignment extra)

### Files
| # | File | What it does |
|---|---|---|
| 1 | `gitops/argocd-application.yaml` | Argo CD `Application`: repo + path `helm/clinic` + `values-gitops.yaml`, auto-sync with prune and self-heal. **Edit `repoURL`.** |
| 2 | `gitops/README.md` | Setup + demo steps. |
| (3) | `gitops-update` job in `ci-cd.yml` | Writes the new SHA into `helm/clinic/values-gitops.yaml` and commits it with `[skip ci]`. |

### Verify
```bash
helm uninstall clinic -n clinic            # let Argo CD own the release
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f gitops/argocd-application.yaml
kubectl -n argocd port-forward svc/argocd-server 8443:443     # https://localhost:8443 (admin)
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
Requires: GHCR packages **public** + at least one green pipeline (so `values-gitops.yaml` has a real SHA).

### Commit / screenshot
```text
feat(gitops): add argo cd application and ci image-tag bump
```
- `m9-argocd.png`: app Synced + Healthy

---

## Phase 12: Terraform, AWS VPC + EKS (M7, 15 pts)

Graded: valid HCL · `init` OK · `plan` non-empty · VPC with ≥2 public subnets · EKS with a node group · `destroy` · **`terraform.tfvars.example`** · **no credentials committed**.

### Files, in order
| # | File | What it does |
|---|---|---|
| 1 | `terraform/versions.tf` | Terraform ≥1.5, AWS provider 5.x, `provider "aws"` with default tags, optional S3 backend (commented). |
| 2 | `terraform/variables.tf` | Region (ap-south-1), names, CIDR, AZ count (validated ≥2), node sizes. |
| 3 | `terraform/main.tf` | `vpc` module: 2 public + 2 private subnets, NAT, ELB subnet tags. `eks` module: cluster 1.33, AL2023 managed node group, add-ons incl. EBS CSI. |
| 4 | `terraform/outputs.tf` | VPC/subnet IDs, cluster name/endpoint, ready-to-run `update-kubeconfig` command. |
| 5 | `terraform/terraform.tfvars.example` | Example inputs (1 graded point). |
| 6 | `terraform/README.md` | What it creates, commands, cost warning. |
| 7 | `terraform/.terraform.lock.hcl` | Created by `terraform init`. **Commit it.** |

### Verify
```bash
cd terraform
terraform init           # screenshot
terraform fmt -check
terraform validate       # "Success! The configuration is valid."  screenshot
terraform plan           # needs AWS credentials (aws configure). Screenshot the "Plan: N to add" line
```
**If you have AWS access:** `terraform apply` (~15–20 min) → screenshot **VPC** and **EKS** in the AWS console (region Mumbai, ap-south-1) → `$(terraform output -raw configure_kubectl)` → `kubectl get nodes` → **`terraform destroy`** the same day (≈ $6–7/day otherwise) → screenshot "Destroy complete!".
**If you don't:** the instructor said in class that the `.tf` files are enough. Submit `init` + `validate` screenshots and say in the README that `apply` wasn't run because there were no credentials.

### Commit / screenshots
```text
infra(terraform): add vpc and eks modules with variables, outputs and tfvars example
```
- `m7-init.png`, `m7-validate.png`, `m7-plan.png`, (`m7-aws-vpc.png`, `m7-aws-eks.png`, `m7-destroy.png` if applied)

---

## Phase 13: Troubleshooting challenge (assignment)

"Intentionally introduce multiple issues… identify, investigate logs and resources, find root cause, fix, verify, document."

### Files
| # | File | Breaks… |
|---|---|---|
| 1 | `troubleshooting/01-image-pull-backoff.yaml` | wrong image tag → **ImagePullBackOff** |
| 2 | `troubleshooting/02-service-no-endpoints.yaml` | wrong label selector → **no endpoints** |
| 3 | `troubleshooting/03-wrong-db-password.sh` | wrong Secret → **CrashLoopBackOff** |
| 4 | `troubleshooting/04-bad-readiness-probe.patch.yaml` | wrong probe path → **Running 0/1, rollout stuck** |
| 5 | `troubleshooting/05-pending-insufficient-cpu.yaml` | 64-CPU request → **Pending** |
| 6 | `troubleshooting/06-broken-ingress.yaml` | wrong service/port → **Ingress 503** |
| 7 | `docs/TROUBLESHOOTING.md` | The write-up: symptom → investigation → root cause → fix → verification for each, with real captured output. |

### Do
For each issue, on your Minikube deployment: break it → screenshot the broken state + the command that reveals the cause → fix it → screenshot the healthy state. Save the images as `docs/screenshots/ts-<n>-broken.png` / `ts-<n>-fixed.png`.

### Commit
```text
docs(troubleshooting): add six failure scenarios with root cause analysis
```

---

## Phase 14: README, screenshots, PPT, video, demo (M10, 5 pts + bonus)

### Files
| # | File | What it does |
|---|---|---|
| 1 | `README.md` | Final report with every section the assignment lists (overview, architecture diagram, tech, setup, Docker, K8s, Helm, Terraform, CI/CD, DevSecOps, monitoring, GitOps, troubleshooting, screenshots, lessons learned). **Replace `YOUR_GITHUB_USERNAME`, `<Your Name>` and the pipeline run URL.** |
| 2 | `docs/screenshots/*.png` | All screenshots. The README already links to these file names. |
| 3 | `docs/PRESENTATION.md` | Slide-by-slide outline for the PPT. |
| 4 | `CareDesk-Final-Presentation.pptx` | **Your PPT, in the repo root** (required by the instructor). |
| 5 | Video link in README | 1–2 minutes, **+5 bonus points**. |

### Live demo script (3 of the 5 M10 points: "commit a change → pipeline runs → deployment updates")
```bash
# 1. change something visible: the greeting in frontend/src/pages/Dashboard.jsx
git commit -am "feat(ui): personalise dashboard greeting"
git push
# 2. show GitHub Actions: test → security → build-scan-push → deploy-kind → gitops-update, all green
# 3. show Argo CD syncing (or: helm upgrade clinic ./helm/clinic -n clinic --set backend.tag=<sha> --set frontend.tag=<sha>)
kubectl get pods -n clinic -w
kubectl get pods -n clinic -o jsonpath='{..image}'     # the new SHA
# 4. refresh http://clinic.local and show the change. Then show Grafana.
```

---

## 2. Grading map: where every point comes from

| Module | Pts | Files | Proof (screenshot) |
|---|---|---|---|
| M1 App | 10 | `backend/app/`, `alembic/versions/0001_*.py`, `requirements.txt`, `frontend/`, `docker-compose.yml` | m1-* |
| M2 Tests | 10 | `backend/tests/` (24 tests), `conftest.py`, `pytest.ini` | m2-pytest |
| M3 Git | 5 | public repo, ≥10 meaningful commits, `.gitignore` | m3-commit-history |
| M4 Docker | 10 | `backend/Dockerfile`, `frontend/Dockerfile` (multi-stage), non-root, compose | m4-* |
| M5 CI/CD | 15 | `.github/workflows/ci-cd.yml` | m5-* + run URL |
| M6 Trivy | 5 | Trivy steps in workflow, `security/README.md` | m6-* + explanation |
| M7 Terraform | 15 | `terraform/*.tf`, `terraform.tfvars.example` | m7-* |
| M8 K8s+Helm | 15 | `k8s/namespace.yaml`, `helm/clinic/` | m8-* |
| M9 Observability | 10 | `/metrics`, `monitoring/`, ServiceMonitor, dashboard | m9-* |
| M10 Docs | 5 | `README.md`, live demo | demo |
| Bonus | +5 | video | link |

---

## 3. Recommended commit sequence (≈22 commits)

```text
 1 chore: add gitignore for python, node, terraform and secrets
 2 feat(api): add settings, database session and ORM models
 3 feat(api): add pydantic schemas with validation
 4 feat(api): add patients, doctors and appointments CRUD routers
 5 feat(api): add health, readiness and prometheus metrics endpoints
 6 feat(db): add alembic migration for clinic tables
 7 feat(api): add demo seed data and wait-for-db startup check
 8 test(api): add conftest with isolated sqlite db and 24 API tests
 9 feat(ui): add react app shell, api client and shared components
10 feat(ui): add dashboard, patients, doctors and appointments pages
11 style(ui): responsive layout for tablet and mobile
12 build(docker): add non-root backend image with healthcheck
13 build(docker): add multi-stage non-root frontend image with nginx template
14 build(compose): add full stack with healthchecks, volume and network
15 ci: add pipeline with tests, image build, ghcr push and kind deploy
16 ci(security): add bandit, pip-audit, npm audit, gitleaks and trivy gates
17 deploy(k8s): add namespace, configmap, secret and app manifests for CI
18 deploy(helm): add clinic chart with configmap, secret, statefulset, ingress and hpa
19 feat(monitoring): add kube-prometheus-stack values, alerts and grafana dashboard
20 feat(gitops): add argo cd application and ci image-tag bump
21 infra(terraform): add vpc and eks modules with variables, outputs and tfvars example
22 docs: add troubleshooting guide, readme, screenshots and presentation
```

---

## 4. Master screenshot checklist (`docs/screenshots/`)

| ✔ | File | What to capture |
|---|---|---|
| ☐ | m1-ui-dashboard.png | Dashboard with seeded data |
| ☐ | m1-ui-create.png | Booking modal open |
| ☐ | m1-ui-mobile.png | DevTools phone view |
| ☐ | m1-swagger.png | `/docs` with all endpoints |
| ☐ | m1-health.png / m1-ready.png | JSON responses |
| ☐ | m1-db-table.png | `\dt` + a `SELECT` |
| ☐ | m2-pytest.png | `pytest -v` → 24 passed |
| ☐ | m3-commit-history.png | GitHub commits page (≥10) |
| ☐ | m3-repo.png | Repo home page (for the PPT) |
| ☐ | m4-compose-up.png | `docker compose up --build` output |
| ☐ | m4-compose-ps.png | 3 services healthy |
| ☐ | m4-nonroot.png | `whoami` → appuser / nginx |
| ☐ | m4-browser.png | http://localhost:3000 |
| ☐ | m5-pipeline-green.png | All 5 jobs green |
| ☐ | m5-pipeline-red-gate.png | Failed test blocks build (bonus) |
| ☐ | m5-ghcr-packages.png | Packages with SHA tags |
| ☐ | m5-kind-deploy-log.png | deploy-kind job: pods Running + smoke test |
| ☐ | m6-trivy-backend.png / m6-trivy-frontend.png | Trivy step output |
| ☐ | m6-security-job.png | security job steps green |
| ☐ | m7-init.png / m7-validate.png / m7-plan.png | Terraform |
| ☐ | m7-aws-vpc.png / m7-aws-eks.png / m7-destroy.png | Only if applied |
| ☐ | m8-namespace.png | `kubectl apply -f k8s/namespace.yaml` |
| ☐ | m8-helm-install.png | Helm install output + NOTES |
| ☐ | m8-get-pods.png | All Running, ≥2 backend + ≥2 frontend |
| ☐ | m8-get-svc.png | ClusterIP services |
| ☐ | m8-helm-list.png | Release deployed |
| ☐ | m8-ingress.png | Browser at http://clinic.local |
| ☐ | m8-hpa.png | HPA scaling under load |
| ☐ | m8-helm-history.png | Upgrade + rollback |
| ☐ | m9-metrics-curl.png | `/metrics` output |
| ☐ | m9-prom-targets.png | Target UP |
| ☐ | m9-grafana-dashboard.png | Dashboard with live data |
| ☐ | m9-argocd.png | Synced / Healthy |
| ☐ | ts-1…6-broken.png / ts-1…6-fixed.png | Troubleshooting before/after |

---

## 5. Common problems while building

| Problem | Cause → fix |
|---|---|
| `Bind for 0.0.0.0:3000 failed: port is already allocated` | Another stack (e.g. TaskBoard) uses the port. Run `docker compose down` there, or `FRONTEND_PORT=3100 BACKEND_PORT=8100 docker compose up`. |
| `ModuleNotFoundError: No module named 'app'` from alembic | `prepend_sys_path = .` is missing in `alembic.ini`, or you aren't in `backend/`. |
| Backend container exits on first start | Postgres not ready. `wait_for_db.py` + the Compose healthcheck handle this. Check `docker compose logs backend`. |
| Frontend shows "Backend unavailable" | Backend not running / not healthy: `docker compose ps`, `docker compose logs backend`. |
| `npm ci` fails in CI | `package-lock.json` wasn't committed. |
| Trivy step fails | A new CVE was published. Update the base image or package, or add it to `security/.trivyignore` **with a reason**. |
| GHCR push `denied` | The workflow needs `permissions: packages: write` (already set). For forks, enable Actions. |
| `gitops-update` push fails (403) | Repo Settings → Actions → Workflow permissions → **Read and write**. |
| Pods `ImagePullBackOff` on Minikube | GHCR package is private, or the tag is wrong. Make it public, or use `values-dev.yaml` with `minikube image load`. |
| HPA `cpu: <unknown>` | `minikube addons enable metrics-server`, then wait about 1 minute. |
| `clinic.local` doesn't open | hosts file entry missing, or `minikube tunnel` not running in an **admin** terminal. |
| Prometheus target missing | Prometheus release isn't named `kube-prometheus-stack`, or the clinic chart was installed before Prometheus. Run `helm upgrade clinic ... --reuse-values`. |
| `terraform plan`: no valid credential sources | Run `aws configure` first (or skip plan, see Phase 12). |

---

## 6. Final submission checklist

```text
[ ] Repo is public; YOUR_GITHUB_USERNAME / <Your Name> replaced everywhere (README, values*.yaml, gitops/)
[ ] docker compose up --build works from a fresh clone
[ ] pytest -v → 24 passed (screenshot)
[ ] ≥10 meaningful commits; .gitignore covers .env, __pycache__, node_modules, .venv
[ ] Both images non-root; frontend multi-stage
[ ] Pipeline green on main; images in GHCR with SHA tags; run URL in README
[ ] Trivy runs on both images and blocks HIGH/CRITICAL; CVE explanation in README
[ ] No secrets in Git (Gitleaks job green)
[ ] terraform init/validate(/plan) screenshots; tfvars.example present; destroy screenshot if applied
[ ] k8s/namespace.yaml; Helm release deployed; pods Running (≥2 each); svc; helm list; Ingress in browser; HPA
[ ] /metrics, Prometheus target UP, Grafana dashboard with data
[ ] docs/TROUBLESHOOTING.md with your own screenshots
[ ] README complete with all screenshots
[ ] PPT in repo root; (bonus) video link in README
[ ] Demo rehearsed: commit → pipeline → new pods
[ ] terraform destroy done if you created AWS resources
```
