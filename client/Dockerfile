FROM python:3.11-alpine

WORKDIR /app

# Install restic and dependencies
RUN apk add --no-cache restic

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 4810

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4810"]
