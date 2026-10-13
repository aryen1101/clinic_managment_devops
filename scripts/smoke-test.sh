#!/usr/bin/env bash

set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:3000}"
pass() { echo "  ✔ $1"; }
fail() { echo "  ✘ $1"; exit 1; }

echo "Smoke testing ${BASE_URL}"
curl -fsS "${BASE_URL}/" -o /dev/null && pass "frontend serves index.html" || fail "frontend"
curl -fsS "${BASE_URL}/health" | grep -q '"UP"' && pass "/health is UP" || fail "/health"
curl -fsS "${BASE_URL}/ready" | grep -q '"READY"' && pass "/ready - database reachable" || fail "/ready"
curl -fsS "${BASE_URL}/api/stats" | grep -q total_patients && pass "/api/stats" || fail "/api/stats"

PID=$(curl -fsS -X POST "${BASE_URL}/api/patients" -H 'Content-Type: application/json' \
  -d '{"full_name":"Smoke Test","date_of_birth":"2000-01-01","gender":"OTHER","phone":"+91 90000 99999"}' \
  | sed -E 's/.*"id":([0-9]+).*/\1/')
[[ "$PID" =~ ^[0-9]+$ ]] && pass "POST /api/patients (id=$PID)" || fail "create patient"
curl -fsS -X PUT "${BASE_URL}/api/patients/${PID}" -H 'Content-Type: application/json' -d '{"address":"updated"}' \
  | grep -q updated && pass "PUT /api/patients/${PID}" || fail "update patient"
code=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "${BASE_URL}/api/patients/${PID}")
[[ "$code" == "204" ]] && pass "DELETE /api/patients/${PID}" || fail "delete patient ($code)"
echo "All smoke tests passed"
