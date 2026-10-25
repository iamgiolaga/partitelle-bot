#!/usr/bin/env bash
# Check that the staging service answers over HTTP before promoting it to prod.
#
# Usage: RENDER_API_KEY=... staging-smoke-check.sh <service-id>
# Env:   RENDER_API_KEY (required)
#        SMOKE_TIMEOUT  seconds to keep retrying, default 180 (the free instance may be waking up)
#        SMOKE_URL      skip the Render API lookup and check this URL (local testing)
# Passes on any HTTP status < 500 (the app answers, even a 404/405 is fine), fails on 5xx or no answer.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: RENDER_API_KEY=... $0 <service-id>" >&2
  exit 2
fi

service_id="$1"
timeout="${SMOKE_TIMEOUT:-180}"
url="${SMOKE_URL:-}"

if [ -z "$url" ]; then
  : "${RENDER_API_KEY:?RENDER_API_KEY is not set}"
  response="$(curl --silent --show-error --fail-with-body \
    --header "Authorization: Bearer ${RENDER_API_KEY}" \
    --header "Accept: application/json" \
    "https://api.render.com/v1/services/${service_id}")"
  url="$(jq -r '.serviceDetails.url // empty' <<<"$response")"
  if [ -z "$url" ]; then
    echo "::error::No public URL found for service ${service_id}" >&2
    exit 1
  fi
fi

deadline=$((SECONDS + timeout))
while true; do
  # Status 000 = no answer (connection error or timeout).
  status="$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 30 "$url" || true)"
  if [ "$status" -ge 100 ] && [ "$status" -lt 500 ]; then
    echo "Staging answered HTTP ${status} at ${url}"
    exit 0
  fi
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "::error::Staging (${url}) did not answer with a status below 500 within ${timeout}s (last status: ${status}). Not promoting."
    exit 1
  fi
  echo "Staging answered ${status} at ${url}, retrying..."
  sleep "${SMOKE_INTERVAL:-10}"
done
