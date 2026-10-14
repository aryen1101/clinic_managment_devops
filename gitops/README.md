# GitOps with Argo CD

**Git is the single source of truth for what runs in the cluster.** CI never runs `kubectl apply` against the real cluster. It only commits a new image tag to Git, and Argo CD (running inside the cluster) pulls the change and applies it.

```text
developer ──git push──► GitHub ──► CI: test → scan → build → push image (tag = SHA)
                                         │
                                         └─► commits helm/clinic/values-gitops.yaml (new SHA) [skip ci]
                                                        │
                      Argo CD (in cluster) ◄── polls ───┘
                             │
                             └─► helm upgrade clinic → rolling update → new pods
```

## Setup (Minikube)

```bash
# 1. Install Argo CD
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-server

# 2. Edit gitops/argocd-application.yaml -> repoURL = your GitHub repo, then:
kubectl apply -f gitops/argocd-application.yaml

# 3. Open the UI
kubectl -n argocd port-forward svc/argocd-server 8443:443
#    https://localhost:8443   user: admin
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Requirements

- The GHCR packages `clinic-backend` and `clinic-frontend` must be **public**. Otherwise create an `imagePullSecret` and set `imagePullSecrets` in `values.yaml`.
- In GitHub, go to **Settings → Actions → General → Workflow permissions** and choose **Read and write**, so the `gitops-update` job can push the tag commit.
- If you installed the app with Helm by hand first, uninstall it (`helm uninstall clinic -n clinic`) so Argo CD owns the release.

## Demo

1. Change something visible, for example the greeting in `frontend/src/pages/Dashboard.jsx`.
2. `git commit -am "feat(ui): new dashboard greeting" && git push`
3. Watch GitHub Actions turn green. The last job commits `chore(gitops): deploy <sha>`.
4. In the Argo CD UI the app goes *OutOfSync → Syncing → Synced/Healthy*.
5. `kubectl get pods -n clinic -o jsonpath='{..image}'` now shows the new SHA.
6. **Self-heal:** `kubectl scale deploy clinic-frontend -n clinic --replicas=5`, and Argo CD (with HPA) brings it back to what Git says.
