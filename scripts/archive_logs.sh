#!/bin/bash
set -e

SERVICE_NAME=$1
DEST_DIR="/tmp/archives/$SERVICE_NAME"
mkdir -p "$DEST_DIR"

echo "Archiving logs for $SERVICE_NAME..."
kubectl logs --all-containers=true -n "$SERVICE_NAME" > "$DEST_DIR/logs.txt"

# Example upload to S3 (optional)
# aws s3 cp "$DEST_DIR/logs.txt" "s3://your-backup-bucket/$SERVICE_NAME/logs.txt"

echo "Logs archived at $DEST_DIR"
