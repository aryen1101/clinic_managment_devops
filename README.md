# 🩺 CareDesk: Clinic Management System (DevSecOps Capstone)

[![Clinic CI/CD](https://github.com/aryen1101/clinic_managment_devops/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/aryen1101/clinic_managment_devops/actions/workflows/ci-cd.yml)

**CareDesk** is a web application for small clinics. Front-desk staff register **patients**, manage **doctors** and their availability, and book, complete or cancel **appointments**. The system prevents a doctor from being double-booked and keeps every patient's visit history.

The application is the vehicle. The project is the **DevSecOps platform around it**: every commit is tested, security-scanned, packaged into container images, pushed to a registry, deployed to Kubernetes, synchronised by GitOps and monitored with Prometheus and Grafana. The cloud infrastructure is described as code with Terraform.

| | |
|---|---|
| **Repository** | https://github.com/aryen1101/clinic_managment_devops |
| **Successful pipeline run** | https://github.com/aryen1101/clinic_managment_devops/actions/runs/38460482398 |
| **Presentation + demo video** | [`demo/`](demo/) |
| **▶️ Watch the demo video online** | [Google Drive](https://drive.google.com/file/d/1ZosvQ1rO4caY2WLrsEr1AtPMkDOQcaNr/view?usp=sharing) |

---

## Contents
1. [Features](#1-features)
2. [Architecture](#2-architecture)
3. [Technology stack](#3-technology-stack)
4. [Repository structure](#4-repository-structure)
5. [Application setup](#5-application-setup)
6. [API reference](#6-api-reference)
7. [Testing](#7-testing)
8. [Git and GitHub](#8-git-and-github)
9. [Docker](#9-docker)
10. [CI/CD pipeline](#10-cicd-pipeline)
11. [DevSecOps](#11-devsecops)
12. [Terraform (AWS infrastructure)](#12-terraform-aws-infrastructure)
13. [Kubernetes](#13-kubernetes)
14. [Helm, Ingress and HPA](#14-helm-ingress-and-hpa)
15. [Observability (Prometheus + Grafana)](#15-observability-prometheus--grafana)
16. [GitOps (Argo CD)](#16-gitops-argo-cd)
17. [Demo video and presentation](#17-demo-video-and-presentation)
18. [Lessons learned](#18-lessons-learned)

---

## 1. Features

| Area | What it does |
|---|---|
| **Dashboard** | KPI cards (patients, doctors, today's appointments, upcoming), today's schedule, appointment-status breakdown, live API and database health |
| **Patients** | Register / edit / delete, search by name or phone, age from date of birth, blood group, full visit history |
| **Doctors** | Add / edit / delete, filter by specialization, consultation fee, one-click availability toggle |
| **Appointments** | Book, reschedule, mark completed, cancel, delete, filter by status or date, doctor's notes |
| **Business rules** | No double-booking of a doctor at the same date/time (HTTP 409), unavailable doctors cannot be booked (HTTP 400), deleting a patient or doctor removes their appointments |
| **Ops endpoints** | `/health` (liveness), `/ready` (readiness, checks the DB), `/metrics` (Prometheus), `/docs` (Swagger) |
| **UI** | Responsive React UI: sidebar on desktop, top bar on tablet, icon bar on phone |

![CareDesk dashboard](screenshots/m1-ui-dashboard.png)

---

## 2. Architecture

```mermaid
flowchart LR
    dev([Developer]) -- git push --> gh[GitHub]
    gh --> ci{{GitHub Actions}}
    subgraph cicd [CI/CD pipeline]
      ci --> t[Test<br/>ruff + 24 pytest<br/>frontend build]
      ci --> s[Security<br/>Bandit · pip-audit · npm audit<br/>Gitleaks · Trivy config]
      t & s --> b[Docker build] --> tv[Trivy image scan<br/>gate: HIGH/CRITICAL] --> reg[(GHCR<br/>tag = commit SHA)]
      reg --> kind[kind cluster<br/>deploy + smoke test]
      kind --> go[Commit new tag to<br/>values-gitops.yaml]
    end
    go --> argo[Argo CD]
    tf[Terraform] -.-> aws[(AWS VPC + EKS)]
    subgraph k8s [Kubernetes cluster]
      argo -- Helm chart --> ing[Ingress nginx<br/>clinic.local]
      ing -- / --> fe[Frontend pods<br/>React + nginx]
      ing -- /api --> be[Backend pods<br/>FastAPI]
      fe -- /api proxy --> be
      be --> db[(PostgreSQL<br/>StatefulSet + PVC)]
      hpa[HPA 2→6] -.scales.-> be
      prom[Prometheus] -- scrapes /metrics --> be
      graf[Grafana] --> prom
    end
```

Request path inside the cluster:

```text
Browser ──► Ingress (clinic.local)
              ├── /             ──► Service clinic-frontend:80   ──► nginx pods (React build)
              └── /api, /docs   ──► Service clinic-backend:8000  ──► FastAPI pods ──► Service clinic-postgres:5432 ──► PostgreSQL (PVC)
```

---

## 3. Technology stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 19, Vite 8, CSS | Fast single-page app; static build served by nginx |
| Backend | Python 3.13, FastAPI, Pydantic v2 | Typed REST API with automatic validation and Swagger docs |
| Database | PostgreSQL 17, SQLAlchemy 2, Alembic | Relational data (patients ↔ appointments ↔ doctors) with versioned migrations |
| Testing | Pytest, pytest-cov, Ruff | 24 API tests on an isolated SQLite database, plus linting |
| Containers | Docker (multi-stage), Docker Compose | Same artifact everywhere; one command for the full local stack |
| CI/CD | GitHub Actions | Test → scan → build → push → deploy on every push to `main` |
| Security | Bandit, pip-audit, npm audit, Gitleaks, Trivy | SAST, SCA, secret scanning, IaC and container scanning |
| Registry | GitHub Container Registry (GHCR) | Free, linked to the repo, authenticated with `GITHUB_TOKEN` |
| IaC | Terraform + `terraform-aws-modules` | AWS VPC + EKS described as code |
| Orchestration | Kubernetes (Minikube locally, kind in CI) | Self-healing, rolling updates, autoscaling |
| Packaging | Helm 3 | One chart, per-environment values, upgrade/rollback |
| GitOps | Argo CD | Git is the single source of truth for the cluster |
| Observability | Prometheus, Grafana, Alertmanager | Metrics, dashboards and alerts |

---

## 4. Repository structure

```text
clinic_managment_devops/
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── main.py               # app, middleware, /health /ready /metrics, routers
│   │   ├── config.py             # settings from env vars (DATABASE_URL or DB_* parts)
│   │   ├── db.py                 # SQLAlchemy engine + session dependency
│   │   ├── models.py             # Doctor, Patient, Appointment tables
│   │   ├── schemas.py            # Pydantic request/response models + validation
│   │   ├── routers/              # patients, doctors, appointments, dashboard
│   │   ├── seed.py               # demo data
│   │   └── wait_for_db.py        # waits for Postgres before migrations
│   ├── alembic/versions/         # 0001_create_clinic_tables.py
│   ├── tests/                    # conftest.py + 24 tests
│   ├── Dockerfile                # non-root (uid 10001), HEALTHCHECK
│   └── requirements.txt / requirements-dev.txt / pytest.ini / ruff.toml / alembic.ini
├── frontend/                     # React + Vite
│   ├── src/                      # App.jsx, api.js, components/, pages/, styles.css
│   ├── nginx.conf.template       # SPA + /api reverse proxy (BACKEND_URL env)
│   └── Dockerfile                # multi-stage: node build → nginx-unprivileged (uid 101)
├── docker-compose.yml            # postgres + backend + frontend
├── .github/workflows/ci-cd.yml   # 5-job CI/CD pipeline
├── security/                     # security notes + .trivyignore
├── k8s/                          # plain manifests (used by CI on kind) + namespace.yaml
├── helm/clinic/                  # Helm chart (ConfigMap, Secret, StatefulSet, Deployments, Ingress, HPA, monitoring)
├── monitoring/                   # kube-prometheus-stack values
├── gitops/                       # Argo CD Application
├── terraform/                    # AWS VPC + EKS
├── scripts/                      # smoke-test, load-test, minikube-up
├── screenshots/                  # all screenshots used in this README
├── demo/                         # presentation (PPT) + demo video (MP4)
└── README.md
```

---

## 5. Application setup

### Option A: Docker Compose (quickest)
```bash
docker compose up --build                         # http://localhost:3000   API docs: http://localhost:8000/docs
docker compose exec backend python -m app.seed    # optional demo data
docker compose down                               # stop (add -v to delete the database volume)
```

### Option B: run backend and frontend directly
```powershell
# Database only (port 5433 avoids clashing with a locally installed PostgreSQL on 5432)
docker run -d --name clinic-db -e POSTGRES_DB=clinic -e POSTGRES_USER=clinic -e POSTGRES_PASSWORD=clinic -p 5433:5432 postgres:17-alpine

# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env        # then set DATABASE_URL=postgresql+psycopg://clinic:clinic@localhost:5433/clinic
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxies /api to :8000)
```

| Swagger UI | Health / readiness |
|---|---|
| ![Swagger](screenshots/m1-swagger.png) | ![Health](screenshots/m1-health.png) ![Ready](screenshots/m1-ready.png) |

**Database:** Alembic migration `0001_create_clinic_tables` creates the `doctors`, `patients` and `appointments` tables:

![Database tables](screenshots/m1-db-table.png)

**Booking form in the UI:**

![Create appointment](screenshots/m1-ui-create.png)

---

## 6. API reference

Interactive documentation is at **`/docs`** (Swagger UI).

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness: process is up |
| GET | `/ready` | Readiness: database reachable (503 if not) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/stats` | Dashboard counters |
| GET / POST | `/api/patients` | List (`?search=`) / register patient |
| GET / PUT / DELETE | `/api/patients/{id}` | Read / update / delete patient |
| GET | `/api/patients/{id}/appointments` | Visit history |
| GET / POST | `/api/doctors` | List (`?specialization=&available=`) / add doctor (409 on duplicate email) |
| GET / PUT / DELETE | `/api/doctors/{id}` | Read / update / delete doctor |
| GET / POST | `/api/appointments` | List (`?status=&date=&doctor_id=&patient_id=`) / book |
| GET / PUT / DELETE | `/api/appointments/{id}` | Read / reschedule / complete / cancel / delete |

**Business rule in action:** booking an appointment returns **201**, and booking the same doctor at the same time again returns **409**:

| First booking (201) | Same slot again (409) |
|---|---|
| ![Create appointment](screenshots/m1-api-crud.png) | ![Double booking rejected](screenshots/m1-double-booking.png) |

---

## 7. Testing

```bash
cd backend
pytest -v          # 24 tests
ruff check .       # lint
```

- **24 tests** in 4 files cover every endpoint group: system (`/`, `/health`, `/ready`, `/metrics`), patients, doctors, appointments and stats.
- Tests **never touch PostgreSQL**. `tests/conftest.py` points `DATABASE_URL` at a temporary SQLite file *before* the app is imported, and recreates empty tables for every test.
- Business rules are tested: double-booking (409), unavailable doctor (400), cascade delete, input validation (422).

![pytest](screenshots/m2-pytest.png)

---

## 8. Git and GitHub

- Public repository with a meaningful, step-by-step commit history (backend → tests → frontend → Docker → CI/CD → Kubernetes → monitoring → GitOps → Terraform).
- `.gitignore` excludes `.env`, `__pycache__/`, `.venv/`, `node_modules/`, Terraform state and `*.tfvars`, so no secrets or build artifacts are committed.
- Commits named `chore(gitops): deploy <sha> [skip ci]` are created automatically by the pipeline's GitOps job (see section 16).

![Commit history](screenshots/m3-commit-history.png)

---

## 9. Docker

| Image | Base | Highlights |
|---|---|---|
| `clinic-backend` | `python:3.13-slim` | Dependency layer cached separately · runs as **non-root uid 10001 (`appuser`)** · `pip` removed after install · `HEALTHCHECK` on `/health` · start: wait for DB → `alembic upgrade head` → uvicorn |
| `clinic-frontend` | **multi-stage**: `node:22-alpine` (build) → `nginx-unprivileged:1.29-alpine` (runtime) | Build tools never reach the runtime image · runs as **non-root uid 101 (`nginx`)** on port 8080 · `apk upgrade` for CVE fixes · nginx config rendered from a template (`BACKEND_URL`) |

`docker-compose.yml` runs 3 services on a private bridge network with a named volume for PostgreSQL. **Healthchecks** make the backend wait for a healthy database and the frontend wait for a healthy backend. PostgreSQL is not published to the host.

```bash
docker compose up --build -d
docker compose ps
docker compose exec backend whoami     # appuser
docker compose exec frontend whoami    # nginx
```

![docker compose up, ps and non-root users](screenshots/m4-docker-terminal.png)
![App on localhost:3000](screenshots/m4-browser.png)

---

## 10. CI/CD pipeline

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every **push** and pull request to **`main`**:

```text
┌──────────────┐
│ test         │ ruff · pytest (24) + coverage · npm ci + vite build
└──────┬───────┘
       │      ┌──────────────┐
       ├──────┤ security     │ Bandit · pip-audit · npm audit · Gitleaks · Trivy config
       ▼      └──────┬───────┘
┌─────────────────────────────┐
│ build-scan-push             │ docker build ×2 → Trivy gate (HIGH/CRITICAL) → push ghcr.io/aryen1101/clinic-*:<commit-sha>
└──────┬──────────────────────┘
       ▼
┌─────────────────────────────┐
│ deploy-kind                 │ temporary kind cluster → kubectl apply k8s/ (this SHA) → rollout status → smoke test
└──────┬──────────────────────┘
       ▼
┌─────────────────────────────┐
│ gitops-update               │ writes the SHA into helm/clinic/values-gitops.yaml → commit [skip ci] → Argo CD syncs
└─────────────────────────────┘
```

- **Quality gate:** images are built only if tests and security checks pass.
- **Traceability:** the image tag is the **Git commit SHA** (never `latest`), so every running pod maps to an exact commit.
- **No stored secrets:** GHCR login uses the built-in `GITHUB_TOKEN`.

**Successful run** (all 5 jobs green): https://github.com/aryen1101/clinic_managment_devops/actions/runs/38460482398

![Pipeline green](screenshots/m5-pipeline-green.png)

**The quality gate works:** a deliberately broken test made the `test` job fail, so no image was built, pushed or deployed. Reverting the change made the pipeline green again.

![Pipeline failed on a broken test](screenshots/m5-pipeline-failed.png)

**Images in GHCR, tagged with the commit SHA:**

![GHCR packages](screenshots/m5-ghcr-packages.png)

---

## 11. DevSecOps

Security is checked at several layers. Each catches a different kind of problem (details in [`security/README.md`](security/README.md)):

| Layer | Tool | What it checks | Blocks pipeline? |
|---|---|---|---|
| SAST | Bandit | Insecure Python code patterns | ✔ |
| SCA | pip-audit, npm audit | Known CVEs in Python and npm dependencies | ✔ |
| Secret scanning | Gitleaks | Passwords and keys anywhere in Git history | ✔ |
| IaC scanning | Trivy config | Misconfigurations in Dockerfiles, K8s, Helm, Terraform | report only |
| Container scanning | Trivy image | CVEs in OS packages and libraries of both images | ✔ (HIGH/CRITICAL with a fix) |
| Runtime hardening | Kubernetes `securityContext` | Non-root, no privilege escalation, all capabilities dropped, read-only root FS (backend) | n/a |

**What Trivy scanned and what the result means:** Trivy scans the OS packages (Debian/Alpine) and language libraries (Python wheels) inside both images against public CVE databases. The pipeline is configured to **fail on any HIGH or CRITICAL vulnerability that has a fix available**. Both images pass with **0 HIGH/CRITICAL findings**, so they are pushed to GHCR. During development the first scan found **47 HIGH CVEs**: 43 in Alpine packages of the nginx base image (e.g. `CVE-2026-33630` in c-ares) and 4 in libraries bundled inside `pip`. I fixed them by running `apk upgrade` in the frontend image and removing `pip` from the backend runtime image.

**Security job in CI:**

![Security job](screenshots/m6-security-job.png)

**Trivy image scan (0 vulnerabilities):**

![Trivy](screenshots/m6-trivy.png)

**Same scanners run locally** (Bandit, pip-audit, npm audit, Gitleaks, Trivy):

![Local scans 1](screenshots/m6-local-scans1.png)
![Local scans 2](screenshots/m6-local-scans2.png)
![Local scans 3](screenshots/m6-local-scans3.png)

---

## 12. Terraform (AWS infrastructure)

[`terraform/`](terraform/) describes the AWS infrastructure the application would run on in production:

```text
AWS (ap-south-1, Mumbai)
└── VPC 10.30.0.0/16
    ├── 2 public subnets   10.30.101.0/24, 10.30.102.0/24   (load balancers, NAT gateway)
    ├── 2 private subnets  10.30.1.0/24,   10.30.2.0/24     (worker nodes)
    ├── internet gateway + NAT gateway
    └── EKS cluster "clinic-eks" (Kubernetes 1.33)
        ├── managed node group: 2 × t3.medium (min 1, max 3), Amazon Linux 2023
        └── add-ons: coredns, kube-proxy, vpc-cni, pod-identity-agent, aws-ebs-csi-driver
```

| File | Purpose |
|---|---|
| `versions.tf` | Terraform + AWS provider versions, provider configuration, default tags |
| `variables.tf` | Inputs (region, names, CIDR, node sizes) with defaults |
| `main.tf` | `terraform-aws-modules/vpc` + `terraform-aws-modules/eks` |
| `outputs.tf` | VPC/subnet IDs, cluster endpoint, ready-made `update-kubeconfig` command |
| `terraform.tfvars.example` | Example inputs. The real `terraform.tfvars` is git-ignored and **no credentials are committed** |
| `.terraform.lock.hcl` | Pins exact provider versions |

```bash
cd terraform
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
```

The configuration was **initialised, validated and planned against a real AWS account**. The plan shows **60 resources to add**: VPC, 2 public + 2 private subnets, NAT gateway, EKS 1.33 cluster, managed node group, IAM roles, security groups and KMS key.

**`terraform apply` was intentionally not run.** The EKS control plane, NAT gateway and t3.medium nodes are not covered by the AWS Free Tier, and the account used is a free-tier account that must not incur charges. The same code creates the full environment with `terraform apply` and removes it with `terraform destroy`.

![terraform init and validate](screenshots/m7-init-validate.png)
![terraform plan: 60 to add](screenshots/m7-plan.png)

---

## 13. Kubernetes

| Object | Purpose |
|---|---|
| `Namespace` `clinic` | Isolation ([`k8s/namespace.yaml`](k8s/namespace.yaml)) |
| `Deployment` backend / frontend | 2+ replicas, rolling updates with `maxUnavailable: 0` |
| `Service` (ClusterIP) × 3 | Stable DNS: `clinic-backend:8000`, `clinic-frontend:80`, `clinic-postgres:5432` |
| `ConfigMap` | APP_ENV, LOG_LEVEL, DB_HOST, DB_PORT, DB_NAME |
| `Secret` | DB_USER, DB_PASSWORD |
| `StatefulSet` + `PVC` (Helm) | PostgreSQL with persistent storage |
| Probes | startup + liveness `/health`, readiness `/ready`, `pg_isready` for Postgres |
| `securityContext` | runAsNonRoot, drop ALL capabilities, no privilege escalation, seccomp RuntimeDefault |

Two ways to deploy:
- **`k8s/`**: plain manifests. CI applies them to a temporary **kind** cluster on every push. Tested locally on kind as well.
- **`helm/clinic/`**: the full chart (next section), used on Minikube and managed by Argo CD.

**Plain manifests on a local kind cluster:** pods, services, ConfigMap and Secret.

![k8s resources](screenshots/m8-k8s-resources.png)
![app via kind](screenshots/m8-k8s-browser.png)

---

## 14. Helm, Ingress and HPA

```bash
minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server
minikube image load clinic-backend:local
minikube image load clinic-frontend:local

kubectl apply -f k8s/namespace.yaml
helm upgrade --install clinic ./helm/clinic -n clinic -f helm/clinic/values-dev.yaml --wait
kubectl exec -n clinic deploy/clinic-backend -- python -m app.seed

kubectl get pods,svc,ingress,hpa,pvc -n clinic
helm list -n clinic
```

**Release deployed:** 2 backend + 2 frontend + PostgreSQL pods all `Running`, ClusterIP services, Ingress `clinic.local`, HPAs and a bound PVC:

![helm deployment](screenshots/m8-helm-terminal.png)

**Ingress:** `127.0.0.1 clinic.local` in the hosts file plus `minikube tunnel`. `/` routes to the frontend, and `/api`, `/docs`, `/health`, `/ready` route to the backend.

![App via Ingress](screenshots/m8-ingress.png)

**Horizontal Pod Autoscaler:** under load (`scripts/load-test.sh`), backend CPU reached **279% of target** and the HPA scaled the backend from **2 to 6 replicas**:

![HPA scaling](screenshots/m8-hpa.png)

**Helm upgrade and rollback:**

![helm history](screenshots/m8-helm-history.png)

---

## 15. Observability (Prometheus + Grafana)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml
```

- **Metrics:** the backend exposes `/metrics` (request count, latency histogram, in-flight requests per endpoint) plus a business metric, `clinic_appointments_booked_total`.
- **ServiceMonitor** (in the Helm chart): Prometheus scrapes every backend pod every 15 seconds.
- **Alerts** (PrometheusRule): `ClinicBackendDown`, `ClinicHighErrorRate` (> 5% 5xx), `ClinicSlowResponses` (p95 > 1 s).
- **Grafana dashboard** "CareDesk Clinic - Application Overview" is provisioned automatically from the chart (11 panels: requests/sec, error rate, p95 latency, pods up, requests by endpoint, status codes, latency percentiles, appointments booked, CPU, memory, replicas).
- **Logs:** one line per request (`method path → status (duration)`), viewable with `kubectl logs -n clinic deploy/clinic-backend`.

**`/metrics` endpoint:**

![metrics](screenshots/m9-metrics-curl.png)

**Prometheus target UP:**

![Prometheus targets](screenshots/m9-prom-targets.png)

**Grafana dashboard with live data:**

![Grafana](screenshots/m9-grafana-dashboard.png)

---

## 16. GitOps (Argo CD)

Git is the single source of truth for what runs in the cluster. CI never runs `kubectl` against the real cluster; it only commits the new image tag, and Argo CD applies it.

```text
git push ──► GitHub Actions: test → scan → build → push image (tag = SHA)
                    └─► commits helm/clinic/values-gitops.yaml (new SHA) [skip ci]
                                         │
Argo CD (in the cluster) ◄── watches ────┘ ──► helm upgrade ──► rolling update ──► new pods
```

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f gitops/argocd-application.yaml
```

The Argo CD Application ([`gitops/argocd-application.yaml`](gitops/argocd-application.yaml)) deploys `helm/clinic` with `values-gitops.yaml`, with **automated sync, prune and self-heal**. Manual changes in the cluster are reverted to what Git says.

![Argo CD synced and healthy](screenshots/m9-argocd.png)

---

## 17. Demo video and presentation

| File | Content |
|---|---|
| [`demo/CareDesk-Presentation.pptx`](demo/CareDesk-Presentation.pptx) | Presentation slides |
| [`demo/CareDesk-Demo.mp4`](demo/CareDesk-Demo.mp4) | Demo video: slides, codebase, a CI/CD pipeline run, Terraform plan, Argo CD sync, Kubernetes, Prometheus and Grafana |

▶️ **Watch the video online (no download needed):** https://drive.google.com/file/d/1ZosvQ1rO4caY2WLrsEr1AtPMkDOQcaNr/view?usp=sharing

---

## 18. Lessons learned

- **Readiness ≠ liveness.** `/health` must not depend on the database (a DB blip would restart every pod), while `/ready` must (traffic should only reach pods that can serve it).
- **Startup order matters.** Backend pods crashed until PostgreSQL was ready. A wait-for-DB step plus a Postgres advisory lock (so several pods don't run migrations at the same time) gave zero restarts.
- **Security scanners find real problems.** Trivy blocked the first build with 47 HIGH CVEs, mostly in base images rather than my code. Patching the base image and removing unused tools fixed it.
- **The pipeline protects the main branch.** A broken test stopped the pipeline before any image was built, and a missing file (`security/.trivyignore`) was found from the Actions logs and fixed.
- **Tag images with the commit SHA.** Every deployment is traceable to a commit, and rollbacks are exact.
- **GitOps changes how you deploy.** With Argo CD self-heal, manual `kubectl` changes are reverted, so all changes go through Git.
- **Cost awareness is part of DevOps.** EKS and NAT gateways cost money even on the free tier, so the infrastructure was validated and planned but not left running.