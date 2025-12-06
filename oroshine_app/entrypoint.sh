#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $PG_HOST $PG_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"
echo "===================================="

# Make migrations
echo "Creating Migrations..."
python manage.py makemigrations
echo "===================================="

# Apply migrations
echo "Applying Migrations..."
python manage.py migrate
echo "===================================="

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "===================================="

# Compress static files (if using django-compressor)
echo "Compressing static files..."
python manage.py compress
echo "===================================="

# Start Django server
echo "Starting Server..."
exec python manage.py runserver 0.0.0.0:8000
