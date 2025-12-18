#!/bin/bash
set -e

# 1. Wait for Database (Needed for Web AND Celery)
echo "Waiting for PostgreSQL..."
while ! nc -z $PG_HOST $PG_PORT; do
  sleep 1
done
echo "PostgreSQL is up."

# 2. Logic: If NO command is passed (Web Container), run setup + Gunicorn.
#           If a command IS passed (Celery), just run that command.
if [ $# -eq 0 ]; then
    # --- WEB SERVER LOGIC ---
    echo "-----------------------------------"
    echo "Running Web Server Setup"
    echo "-----------------------------------"

    # ✅ ADDED: Make migrations (Use with caution in production)
    echo "Checking for changes (makemigrations)..."
    python manage.py makemigrations --noinput

    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    # ✅ ADDED: Compression for Performance
    # This might take 10-20 seconds and use Swap memory
    echo "Compressing static files..."
    python manage.py compress --force

    echo "Starting Gunicorn..."
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
else
    # --- CELERY/WORKER LOGIC ---
    echo "-----------------------------------"
    echo "Executing Custom Command: $@"
    echo "-----------------------------------"
    exec "$@"
fi