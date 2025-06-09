# Use Python 3.8 slim as base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy setup files
COPY setup.py .
COPY README.md .
COPY app/ app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 4800

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4800"] 