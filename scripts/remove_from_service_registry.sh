#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service_name>}"

echo "Removing $SERVICE_NAME from registry..."
# MOCKED — wire this up to your real service discovery / registry API.
# Example: curl -sf -X DELETE "https://registry.internal/api/services/${SERVICE_NAME}"

echo "Removed from service registry (mocked) for $SERVICE_NAME"
