#!/usr/bin/env bash
# One-shot local Kubernetes deployment on Minikube with the Helm chart, using locally built images.
#   ./scripts/minikube-up.sh
# Afterwards: add "127.0.0.1 clinic.local" to your hosts file, run `minikube tunnel` (admin terminal), open http://clinic.local
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Starting minikube"
minikube status >/dev/null 2>&1 || minikube start --cpus=4 --memory=6g
minikube addons enable ingress
minikube addons enable metrics-server

echo "==> Building images and loading them into minikube"
docker compose build
minikube image load clinic-backend:local
minikube image load clinic-frontend:local

echo "==> Namespace + Helm release"
kubectl apply -f k8s/namespace.yaml
helm upgrade --install clinic ./helm/clinic -n clinic -f helm/clinic/values-dev.yaml --wait --timeout 5m

echo "==> Demo data"
kubectl exec -n clinic deploy/clinic-backend -- python -m app.seed

kubectl get pods,svc,ingress,hpa -n clinic
helm list -n clinic
