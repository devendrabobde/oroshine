FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including curl for the download script
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make scripts executable
RUN chmod +x entrypoint.sh download_static.sh

# Run the static download script during build to ensure files exist
# We temporarily move to the root where the script expects to run or adjust paths
RUN ./download_static.sh

# Fix for 404 Fonts: Ensure the target directory exists and permissions are right
RUN mkdir -p /app/staticfiles && chmod -R 755 /app/staticfiles

CMD ["./entrypoint.sh"]