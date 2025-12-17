# FROM python:3.12-slim

# WORKDIR /app

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Install system dependencies including curl for the download script
# RUN apt-get update && apt-get install -y \
#     netcat-traditional \
#     postgresql-client \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# # Make scripts executable
# RUN chmod +x entrypoint.sh download_static.sh

# # Run the static download script during build to ensure files exist
# # We temporarily move to the root where the script expects to run or adjust paths
# RUN ./download_static.sh

# # Fix for 404 Fonts: Ensure the target directory exists and permissions are right

# RUN mkdir -p /app/staticfiles && chmod -R 755 /app/staticfiles

# CMD ["./entrypoint.sh"]





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
