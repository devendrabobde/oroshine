# Use official Python slim image
FROM python:3.11-slim

# Set unbuffered output for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Copy entrypoint script and give execution permission
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden)
CMD ["gunicorn", "oroshine_app.wsgi:application", "--bind", "0.0.0.0:8000"]




#Testing purpose :
# FROM python:3.11.4-slim-buster

# # Set unbuffered output for python
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Create app directory
# WORKDIR /home/devendra/projects/oroshine/oroshine_app

# # Install app dependencies
# RUN apt-get update && apt-get install -y netcat gcc python3-dev libpq-dev
# RUN pip install --upgrade pip
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# # RUN chmod +x /home/devendra/projects/oroshine/oroshine_app/django.sh

# # Bundle app source
# COPY . .

# # Expose port
# EXPOSE 8000

# # entrypoint to run the django.sh file
# ENTRYPOINT ["/bin/sh", "/home/devendra/projects/oroshine/oroshine_app/entrypoint.sh"]


# ✅ Use bullseye instead of buster (buster repos are dead)
# FROM python:3.11.4-slim

# # Set unbuffered output for python
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Create app directory
# WORKDIR /home/devendra/projects/oroshine/oroshine_app

# # Install dependencies
# RUN apt-get update \&& apt-get install -y \
#     netcat \
#     gcc \
#     python3-dev \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*   # cleanup to reduce image size

# # Upgrade pip
# RUN pip install --upgrade pip

# # Copy requirements first (better caching)
# COPY requirements.txt .

# # Install python packages
# RUN pip install -r requirements.txt

# # Copy application source
# COPY . .

# # Expose port
# EXPOSE 8000

# # Entrypoint to run the django.sh (or entrypoint.sh)
# ENTRYPOINT ["/bin/sh", "/home/devendra/projects/oroshine/oroshine_app/entrypoint.sh"]



# FROM python:3.11-slim

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /home/devendra/projects/oroshine/oroshine_app

# # Install build deps and netcat (openbsd provider)
# RUN apt-get update \
#  && apt-get install -y --no-install-recommends \
#     netcat-openbsd \
#     gcc \
#     python3-dev \
#     libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# # Upgrade pip
# RUN pip install --upgrade pip

# # Copy requirements first to leverage Docker cache
# COPY requirements.txt .

# RUN pip install -r requirements.txt

# # Copy application
# COPY . .

# EXPOSE 8000

# ENTRYPOINT ["/bin/sh", "/home/devendra/projects/oroshine/oroshine_app/entrypoint.sh"]





# ========================
# Stage 1: Builder
# ========================
# FROM python:3.11-slim

# # Set unbuffered output for python
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# WORKDIR /app

# # Install system dependencies for psycopg2
# RUN apt-get update && apt-get install -y \
#     gcc \
#     python3-dev \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# # Copy project files
# COPY . .

# # Run the app
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

