#!/usr/bin/env bash
# Deploy a specific commit to a Render service and wait until it is live.
#
# Usage: RENDER_API_KEY=... render-deploy.sh <service-id> <commit-sha>
# Env:   RENDER_API_KEY (required), DEPLOY_TIMEOUT_SECONDS (default 900), POLL_INTERVAL_SECONDS (default 10)
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: RENDER_API_KEY=... $0 <service-id> <commit-sha>" >&2
  exit 2
fi

service_id="$1"
commit_sha="$2"
: "${RENDER_API_KEY:?RENDER_API_KEY is not set}"
timeout="${DEPLOY_TIMEOUT_SECONDS:-900}"
interval="${POLL_INTERVAL_SECONDS:-10}"
api="https://api.render.com/v1/services/${service_id}/deploys"

echo "Triggering deploy of ${commit_sha} on service ${service_id}"
response="$(curl --silent --show-error --fail-with-body \
  --request POST "$api" \
  --header "Authorization: Bearer ${RENDER_API_KEY}" \
  --header "Accept: application/json" \
  --header "Content-Type: application/json" \
  --data "$(jq -n --arg sha "$commit_sha" '{commitId: $sha}')")"

deploy_id="$(jq -r '.id // .deploy.id // empty' <<<"$response")"
if [ -z "$deploy_id" ]; then
  echo "Render did not return a deploy id (deploy queued or unexpected response): ${response}" >&2
  exit 1
fi
echo "Deploy ${deploy_id} created"

deadline=$((SECONDS + timeout))
while [ "$SECONDS" -lt "$deadline" ]; do
  status="$(curl --silent --show-error --fail-with-body \
    --header "Authorization: Bearer ${RENDER_API_KEY}" \
    --header "Accept: application/json" \
    "${api}/${deploy_id}" | jq -r '.status')"
  echo "Deploy ${deploy_id} status: ${status}"
  case "$status" in
    live)
      echo "Deploy succeeded"
      exit 0
      ;;
    build_failed | update_failed | pre_deploy_failed | canceled | deactivated)
      echo "Deploy ended with status: ${status}" >&2
      exit 1
      ;;
  esac
  sleep "$interval"
done

echo "Timed out after ${timeout}s waiting for deploy ${deploy_id}" >&2
exit 1
