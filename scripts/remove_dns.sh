#!/bin/bash
set -e

SERVICE_NAME=$1
echo "Cleaning DNS entry for $SERVICE_NAME..."

# Example: Route53 deletion
# aws route53 change-resource-record-sets --hosted-zone-id Z123 --change-batch file://delete-record.json

echo "DNS entry removed (mocked)"
