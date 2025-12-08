#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $PG_HOST $PG_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "===================================="
echo "Creating Migrations..."
python manage.py makemigrations

echo "Applying Migrations..."
python manage.py migrate
echo "===================================="

# Note: We already ran collectstatic in Dockerfile, but running it again 
# here is safe and ensures any volume-mounted changes are caught.
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "===================================="
echo "Starting Production Server (Gunicorn)..."
# Use Gunicorn for production instead of runserver
exec gunicorn oroshine.wsgi:application --bind 0.0.0.0:8000 --workers 3