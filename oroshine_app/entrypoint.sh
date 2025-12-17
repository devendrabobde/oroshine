#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
timeout 30 bash -c 'until nc -z $PG_HOST $PG_PORT; do sleep 1; done' || {
  echo "PostgreSQL connection timeout"
  exit 1
}

echo "PostgreSQL is up."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compressing static files..."
# python manage.py compress --force

echo"run the app "

echo "Starting Gunicorn..."
exec gunicorn oroshine_app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 60 \
    --graceful-timeout 30 \
    --max-requests 200 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level warning
