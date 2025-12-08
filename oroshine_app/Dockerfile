# Use slim-bullseye for a smaller image
FROM python:3.11.4-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install system dependencies (curl is needed for your download script)
RUN apt-get update && apt-get install -y \
    netcat \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
# Add gunicorn to production install
RUN pip install -r requirements.txt gunicorn

# Copy application source
COPY . .

# --- STATIC FILES SETUP ---
# Make scripts executable
RUN chmod +x entrypoint.sh download_static.sh

# Run the download script NOW (during build) to fetch CSS/JS libs
RUN ./download_static.sh

# Collect static files (moves everything to STATIC_ROOT)
# We run this here so the image is fully self-contained
RUN python manage.py collectstatic --noinput
# --------------------------

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]