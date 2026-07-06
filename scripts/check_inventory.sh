#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-}"
SERVICES_FILE="services.yaml"

if [[ -z "$SERVICE_NAME" ]]; then
  echo "Usage: $0 <service_name>" >&2
  exit 1
fi

if [[ ! -f "$SERVICES_FILE" ]]; then
  echo "ERROR: $SERVICES_FILE not found" >&2
  exit 1
fi

# Exact match against YAML list entries ("  - name"), not a loose substring
# grep — avoids "auth" incorrectly matching a hypothetical "authz" entry.
if ! grep -qE "^\s*-\s*${SERVICE_NAME}\s*$" "$SERVICES_FILE"; then
  echo "ERROR: '$SERVICE_NAME' not found in $SERVICES_FILE — refusing to decommission an unlisted service" >&2
  exit 1
fi

echo "OK: '$SERVICE_NAME' found in services inventory"
