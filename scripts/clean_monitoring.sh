#!/bin/bash
set -e

SERVICE_NAME=$1
echo "Cleaning up monitoring for $SERVICE_NAME..."

# Example: remove from Datadog
# curl -X DELETE "https://api.datadoghq.com/api/v1/monitor?name=$SERVICE_NAME"

echo "Monitoring cleaned (mocked)"
