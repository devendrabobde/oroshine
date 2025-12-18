#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
# Using nc -z directly
while ! nc -z $PG_HOST $PG_PORT; do
  sleep 1
done
echo "PostgreSQL is up."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
# This moves files from /app/oroshine_webapp/static (downloaded in build)
# TO /app/staticfiles (which is mounted to Nginx)
python manage.py collectstatic --noinput --clear

# OPTIMIZATION: Skipped 'compress' to save memory on t2.micro. 
# If you really need it, enable it, but it might crash the swap.
# python manage.py compress --force 

echo "Starting Gunicorn..."
# Reduced workers to 2 for t2.micro (1GB RAM)
exec gunicorn oroshine_app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-class gthread \
    --timeout 60 \
    --max-requests 1000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info