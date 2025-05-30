#!/bin/bash
set -e

SERVICE_NAME=$1
echo "Removing $SERVICE_NAME from registry..."

# Example: API call to your service discovery system
# curl -X DELETE https://registry.internal/api/services/$SERVICE_NAME

echo "Removed from service registry (mocked)"
