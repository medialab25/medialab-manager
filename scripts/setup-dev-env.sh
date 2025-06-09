#!/bin/bash

# Create .env.dev from template if it doesn't exist
if [ ! -f .env.dev ]; then
    cat > .env.dev << EOL
# Development environment configuration
ENVIRONMENT=development

# Docker configuration
DOCKERFILE=.devcontainer/Dockerfile
DOCKER_SOCKET=/var/run/docker.sock

# Mount configurations
DEV_MOUNT=.:/workspace
CLIENT_MOUNT=./client:/app

# Command overrides for development
API_COMMAND=uvicorn app.main:app --host 0.0.0.0 --port 4800 --reload
CLIENT_COMMAND=uvicorn main:app --host 0.0.0.0 --port 4810 --reload
EOL
    echo "Created .env.dev file"
else
    echo ".env.dev already exists"
fi

# Make the script executable
chmod +x scripts/setup-dev-env.sh 