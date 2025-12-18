# STAGE 1: Build binaries
FROM python:3.12-slim as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# STAGE 2: Runtime
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 netcat-traditional dos2unix curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

COPY . .

# FIX A: Correct the path in download_static.sh dynamically
RUN sed -i 's|TARGET_DIR=.*|TARGET_DIR="/app/oroshine_webapp/static"|g' download_static.sh

# Fix line endings and permissions
RUN dos2unix entrypoint.sh download_static.sh && \
    chmod +x entrypoint.sh download_static.sh && \
    mkdir -p /app/staticfiles /app/media

# Run static download at build time to save deployment time
RUN ./download_static.sh

ENTRYPOINT ["./entrypoint.sh"]