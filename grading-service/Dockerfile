FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y libpq-dev postgresql-client && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 