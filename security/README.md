# DevSecOps — Security Controls

Security is checked at several layers. Each layer catches a different kind of problem, and no single scanner is enough on its own.

| Layer | Tool | What it checks | Where | Blocks the pipeline? |
|---|---|---|---|---|
| **SAST** (static code analysis) | Bandit | Insecure Python code patterns (hard-coded passwords, `eval`, SQL built from strings, weak crypto, etc.) | `security` job | Yes (medium+ severity) |
| **SCA** (dependency scanning) | pip-audit | Known CVEs in `backend/requirements.txt` | `security` job | Yes |
| **SCA** | npm audit | Known CVEs in the frontend's npm packages | `security` job | Yes (high+) |
| **Secret scanning** | Gitleaks | API keys, tokens and passwords committed anywhere in Git history | `security` job | Yes |
| **IaC scanning** | Trivy `config` | Misconfigurations in Dockerfiles, Kubernetes YAML, Helm and Terraform | `security` job | No (report only, see below) |
| **Container scanning** | Trivy `image` | CVEs in OS packages and libraries inside both built images | `build-scan-push` job | **Yes, on HIGH/CRITICAL with a fix available** |
| **Runtime hardening** | Kubernetes `securityContext` | Non-root user, no privilege escalation, all Linux capabilities dropped, read-only root FS (backend) | `k8s/`, `helm/` | n/a |

## The security gate

```text
pytest ─┐
        ├─► build ─► Trivy scan ──(HIGH/CRITICAL found)──► ✖ pipeline fails, nothing is pushed
security┘                      └──(clean)───────────────► push to GHCR ─► deploy
```

An image reaches the registry only if every test and every scanner passes.

## What Trivy found during development (example for the viva)

On the first local scan, **both images failed the gate**:

1. **Frontend:** the `nginx-unprivileged:1.29-alpine` base image (Alpine 3.23.4) had **43 HIGH CVEs** in OS packages, for example `CVE-2026-33630` in **c-ares**, a use-after-free/double-free bug in DNS query handling. Fixed versions already existed in the Alpine repositories.
   **Fix:** `RUN apk upgrade --no-cache` in the runtime stage of `frontend/Dockerfile`.
2. **Backend:** 4 HIGH findings, including `CVE-2026-97687` in **urllib3**, inside libraries *vendored by pip itself*. The app never uses pip at runtime.
   **Fix:** `pip uninstall -y pip` after installing requirements in `backend/Dockerfile`. This shrinks the attack surface.

After the fixes, both scans returned **0 HIGH/CRITICAL** (exit code 0). CVE databases update every day, so a later scan can find new issues. That is expected, and it's why the scan runs on every commit.

## Why the IaC scan is "report only"

The Terraform code uses the public `terraform-aws-modules`, and the EKS API endpoint is intentionally public, so `kubectl` can reach it from a student laptop. Trivy reports both as findings. They are accepted risks for a classroom environment and are documented here rather than silently ignored. In production you would restrict `cluster_endpoint_public_access_cidrs` and turn the IaC scan into a blocking gate.

## Accepting a finding (`.trivyignore`)

If a CVE has no fix yet, or doesn't apply to us, add its ID to `security/.trivyignore` **with a comment explaining why** and a date to review it. Never ignore a finding without a reason.

## Secrets handling

- No credentials in Git. `.env`, `*.tfvars` and kubeconfig files are git-ignored, and Gitleaks enforces this.
- CI uses the built-in `GITHUB_TOKEN` to push to GHCR. No personal tokens are stored.
- Kubernetes: DB credentials live in a `Secret`, and non-secret settings in a `ConfigMap`. The demo password in `k8s/config.yaml` and `helm/clinic/values.yaml` is for throw-away local clusters only. For EKS, `values-prod.yaml` uses `existingSecret`, so the Secret is created outside Git.
- AWS: credentials come from `aws configure` on your laptop, never from files in the repo.
