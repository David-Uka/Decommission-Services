#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service_name>}"
DEST_DIR="/tmp/archives/$SERVICE_NAME"
mkdir -p "$DEST_DIR"

echo "Archiving logs for $SERVICE_NAME..."
kubectl logs --all-containers=true -n "$SERVICE_NAME" > "$DEST_DIR/logs.txt"

# Optional: ship to durable storage. Uncomment and set BACKUP_BUCKET to enable.
# if [[ -n "${BACKUP_BUCKET:-}" ]]; then
#   aws s3 cp "$DEST_DIR/logs.txt" "s3://${BACKUP_BUCKET}/$SERVICE_NAME/logs.txt"
# fi

echo "Logs archived at $DEST_DIR"
