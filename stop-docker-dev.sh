#!/bin/bash

# Stop and remove the medialab-manager-dev container if it's running
echo "Stopping medialab-manager-dev container..."

docker stop medialab-manager-dev 2>/dev/null || true
docker rm medialab-manager-dev 2>/dev/null || true

echo "Docker development environment stopped." 