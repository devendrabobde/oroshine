# #!/bin/bash
# set -e

# echo "Waiting for PostgreSQL..."
# while ! nc -z "$PG_HOST" "$PG_PORT"; do
#   sleep 0.5
# done

# echo "PostgreSQL is up."

# python manage.py makemigrations --noinput
# python manage.py migrate --noinput

# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# echo "Compressing static files..."
# python manage.py compress --force || true

# echo "Starting gunicorn..."
# exec gunicorn oroshine_app.wsgi:application \
#   --bind 0.0.0.0:8000 \
#   --workers 3 \
#   --timeout 120 \
#   --access-logfile - \
#   --error-logfile -







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

echo "compressing static files..."
python manage.py compress --force  

echo "Starting gunicorn with optimized settings..."
exec gunicorn oroshine_app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 4\
  --worker-class gthread \
  --worker-tmp-dir /dev/shm \
  --timeout 60 \
  --graceful-timeout 30 \
  --max-requests 400 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile - \
  --log-level warning