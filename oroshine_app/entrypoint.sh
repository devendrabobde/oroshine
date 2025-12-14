#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z "$PG_HOST" "$PG_PORT"; do
  sleep 0.5
done

echo "PostgreSQL is up."

python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compressing static files..."
python manage.py compress --force || true

echo "Starting gunicorn..."
exec gunicorn oroshine_app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
