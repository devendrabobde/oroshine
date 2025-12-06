# Use slim-bullseye for a smaller image
FROM python:3.11.4-slim-bullseye

# Set unbuffered output for python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    netcat \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint to run your script
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
