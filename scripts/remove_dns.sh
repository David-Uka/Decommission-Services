#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service_name>}"

echo "Cleaning DNS entry for $SERVICE_NAME..."
# MOCKED — wire this up to your real DNS provider.
# Example (Route53): aws route53 change-resource-record-sets \
#   --hosted-zone-id "$HOSTED_ZONE_ID" --change-batch "file://delete-${SERVICE_NAME}.json"

echo "DNS entry removed (mocked) for $SERVICE_NAME"
