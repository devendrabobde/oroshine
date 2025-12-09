#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
MAX_ATTEMPTS=15
COUNT=0
until nc -z $PG_HOST $PG_PORT; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_ATTEMPTS ]; then
    echo "PostgreSQL did not start in time, exiting..."
    exit 1
  fi
  sleep 0.5
done
echo "PostgreSQL started successfully"
python manage.py makemigrations --noinput
echo "===================================="
echo "Applying Migrations..."
python manage.py migrate --noinput
echo "===================================="

echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "===================================="

# echo "compressing static files..."
# python manage.py compress --force 
# echo "===================================="


echo "Starting Production Server (Gunicorn)..."
exec gunicorn oroshine_app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --access-logfile - \
    --error-logfile -
