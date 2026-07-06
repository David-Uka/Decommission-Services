#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service_name>}"

echo "Cleaning up monitoring for $SERVICE_NAME..."
# MOCKED — wire this up to your real observability stack.
# Example (Datadog): curl -sf -X DELETE "https://api.datadoghq.com/api/v1/monitor?name=${SERVICE_NAME}"

echo "Monitoring cleaned (mocked) for $SERVICE_NAME"
