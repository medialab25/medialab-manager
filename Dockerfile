# Pull the base image first
FROM registry.spongnet.uk/python:ml-latest

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4800

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4800"] 