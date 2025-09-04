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
FROM python:3.11.4-slim-bullseye

# Set unbuffered output for python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /home/devendra/projects/oroshine/oroshine_app

# Install dependencies
RUN apt-get update && apt-get install -y \
    netcat \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*   # cleanup to reduce image size

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first (better caching)
COPY requirements.txt .

# Install python packages
RUN pip install -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint to run the django.sh (or entrypoint.sh)
ENTRYPOINT ["/bin/sh", "/home/devendra/projects/oroshine/oroshine_app/entrypoint.sh"]
