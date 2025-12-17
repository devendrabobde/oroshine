
# Use slim Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    postgresql-client \
    curl \
    bash \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure scripts have LF endings and are executable
RUN dos2unix entrypoint.sh download_static.sh \
    && chmod +x entrypoint.sh download_static.sh

# Run the static download script at build time
RUN ./download_static.sh

# Create staticfiles directory and fix permissions
RUN mkdir -p /app/staticfiles && chmod -R 755 /app/staticfiles

# Use entrypoint.sh as the container entrypoint
CMD ["./entrypoint.sh"]
