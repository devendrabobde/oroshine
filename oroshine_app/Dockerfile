# STAGE 1: Build wheels
FROM python:3.12-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# STAGE 2: Runtime
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 netcat-traditional dos2unix curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/*

COPY . /app

RUN dos2unix /app/entrypoint.sh /app/download_static.sh && \
    chmod +x /app/entrypoint.sh /app/download_static.sh && \
    mkdir -p /app/staticfiles /app/media

# Optional: pre-download static assets
RUN /app/download_static.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
