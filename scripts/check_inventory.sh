#!/bin/bash
set -e

SERVICE_NAME=$1
SERVICES_FILE="services.yaml"

if ! grep -q "$SERVICE_NAME" "$SERVICES_FILE"; then
  echo "$SERVICE_NAME not found in services.yaml"
  exit 1
else
  echo "✅ $SERVICE_NAME found in services inventory"
fi
