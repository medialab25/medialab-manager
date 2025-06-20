# Pull the base image first
FROM registry.spongnet.uk/python:ml-latest

WORKDIR /app

# Copy only the app directory and requirements
COPY app/ /app/app/
COPY app/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt debugpy

EXPOSE 4800 4801

# Use debugpy for remote debugging
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:4801", "--wait-for-client", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4800"] 