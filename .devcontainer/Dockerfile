# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install development tools
RUN pip install --no-cache-dir \
    black \
    flake8 \
    pytest \
    pytest-cov \
    ipython

# Copy setup files
COPY setup.py .
COPY README.md .
COPY app/ app/

# Install Python dependencies in development mode
RUN pip install -e ".[dev]"

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# Expose the port the app runs on
EXPOSE 4800

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4800", "--reload"] 