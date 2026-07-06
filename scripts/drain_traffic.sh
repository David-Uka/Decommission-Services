#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service_name>}"

echo "Draining traffic for $SERVICE_NAME..."
kubectl scale deployment "$SERVICE_NAME" --replicas=0 -n "$SERVICE_NAME"
kubectl delete svc "$SERVICE_NAME" -n "$SERVICE_NAME" || echo "Service already removed"

echo "Traffic drained for $SERVICE_NAME"
