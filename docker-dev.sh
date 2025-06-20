#!/bin/bash

# Combined Docker development script
# Usage: ./docker-dev.sh [build|run|publish|push|pull|stop]

set -e

# Configuration
REGISTRY="registry.spongnet.uk"
USERNAME="mediadev"
PASSWORD="MediaMonkey25!!"
IMAGE_NAME="medialab-manager"
DEV_TAG="latest-dev"
PROD_TAG="ml-latest"
CONTAINER_NAME="medialab-manager-dev"
PORT="4801"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Docker login function
docker_login() {
    log_info "Logging into registry..."
    echo "$PASSWORD" | docker login $REGISTRY -u $USERNAME --password-stdin
}

# Build function
build() {
    log_info "Building Docker image..."
    docker build -t $REGISTRY/$IMAGE_NAME:$DEV_TAG .
    log_success "Image built successfully: $REGISTRY/$IMAGE_NAME:$DEV_TAG"
}

# Run function
run() {
    log_info "Starting development container..."
    docker run --rm \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -v $(pwd)/app:/code/app \
        -v $(pwd)/config.json:/code/config.json \
        -v $(pwd)/requirements.txt:/code/requirements.txt \
        $REGISTRY/$IMAGE_NAME:$DEV_TAG \
        uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
}

# Publish function (build and push production tag)
publish() {
    log_info "Publishing production image..."
    docker_login
    docker build -t $REGISTRY/$IMAGE_NAME:$PROD_TAG .
    docker push $REGISTRY/$IMAGE_NAME:$PROD_TAG
    log_success "Production image published: $REGISTRY/$IMAGE_NAME:$PROD_TAG"
}

# Push function (build and push dev tag)
push() {
    log_info "Pushing development image..."
    docker_login
    docker build -t $REGISTRY/$IMAGE_NAME:$DEV_TAG .
    docker push $REGISTRY/$IMAGE_NAME:$DEV_TAG
    log_success "Development image pushed: $REGISTRY/$IMAGE_NAME:$DEV_TAG"
}

# Pull function
pull() {
    log_info "Pulling image from registry..."
    docker_login
    docker pull $REGISTRY/python:$PROD_TAG
    log_success "Image pulled successfully"
}

# Stop function
stop() {
    log_info "Stopping development container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    log_success "Development environment stopped"
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the development Docker image"
    echo "  run       Run the development container"
    echo "  publish   Build and push production image"
    echo "  push      Build and push development image"
    echo "  pull      Pull image from registry"
    echo "  stop      Stop and remove development container"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  $0 publish"
}

# Main script logic
case "${1:-}" in
    build)
        build
        ;;
    run)
        run
        ;;
    publish)
        publish
        ;;
    push)
        push
        ;;
    pull)
        pull
        ;;
    stop)
        stop
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 