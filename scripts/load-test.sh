#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-clinic}"
RELEASE="${RELEASE:-clinic}"
WORKERS="${WORKERS:-20}"
DURATION="${DURATION:-180}"
TARGET="http://${RELEASE}-backend:8000"

echo "Load test: ${WORKERS} workers for ${DURATION}s against ${TARGET} (namespace ${NAMESPACE})"
kubectl -n "$NAMESPACE" delete pod load-generator --ignore-not-found >/dev/null

kubectl -n "$NAMESPACE" run load-generator --rm -i --restart=Never --image=curlimages/curl --quiet -- sh -c "
  end=\$((\$(date +%s) + ${DURATION}))
  worker() {
    while [ \$(date +%s) -lt \$end ]; do
      curl -s -o /dev/null ${TARGET}/api/stats
      curl -s -o /dev/null ${TARGET}/api/appointments
      curl -s -o /dev/null ${TARGET}/api/patients
    done
  }
  i=0; while [ \$i -lt ${WORKERS} ]; do worker & i=\$((i+1)); done
  wait
  echo 'Load test finished'
"
