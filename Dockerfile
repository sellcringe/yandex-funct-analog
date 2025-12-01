FROM python:3.13

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# системные зависимости по минимуму
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# копируем только то, что нужно приложению
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y cron


COPY common/ common/
COPY server/ server/
COPY runner.py runner.py
COPY functions/ functions/
COPY cron_runner.py cron_runner.py

# функции НЕ копируем — они будут примонтированы read-only
# сертификат CH монтируем как volume (см. compose)

CMD ["gunicorn", "server.asgi:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "-b", "0.0.0.0:8080", \
     "--timeout", "120"]
