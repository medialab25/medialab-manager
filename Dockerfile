FROM python:3.11-slim

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4800

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4800"] 