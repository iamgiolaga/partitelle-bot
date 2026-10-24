#!/usr/bin/env bash
# Print the commit SHA currently live on a Render service (latest deploy with status `live`).
#
# Usage: RENDER_API_KEY=... render-live-commit.sh <service-id>
# Env:   RENDER_API_KEY (required)
# Render marks a deploy `deactivated` once a newer one goes live, so the most recent `live` deploy is what runs now.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: RENDER_API_KEY=... $0 <service-id>" >&2
  exit 2
fi

service_id="$1"
: "${RENDER_API_KEY:?RENDER_API_KEY is not set}"

response="$(curl --silent --show-error --fail-with-body \
  --header "Authorization: Bearer ${RENDER_API_KEY}" \
  --header "Accept: application/json" \
  "https://api.render.com/v1/services/${service_id}/deploys?limit=20")"

# The list is newest first; each item is {"deploy": {...}, "cursor": "..."}.
sha="$(jq -r '[.[] | (.deploy // .) | select(.status == "live")] | first | .commit.id // empty' <<<"$response")"

if [ -z "$sha" ]; then
  echo "No live deploy with a commit found among the last 20 deploys of service ${service_id}" >&2
  exit 1
fi

echo "$sha"
