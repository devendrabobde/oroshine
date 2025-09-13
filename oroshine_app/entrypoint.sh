#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL..."
until nc -z $PG_HOST $PG_PORT; do
  sleep 1
done
echo "PostgreSQL started"

# Run Django migrations automatically
python manage.py migrate --noinput

# Collect static files (optional for production)
python manage.py collectstatic --noinput

# Run the server based on environment
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Starting Gunicorn server..."
    gunicorn oroshine_app.wsgi:application --bind 0.0.0.0:8000
fi





#Testing purpose :
# #!/bin/bash
# set -e

# # Wait for the DB to be ready
# echo "Waiting for PostgreSQL to start..."
# while ! nc -z "$PG_HOST" "$PG_PORT"; do
#   sleep 1
# done
# echo "PostgreSQL started!"

# # Run migrations and collect static files
# python manage.py migrate --noinput
# python manage.py collectstatic --noinput

# # Decide whether to run dev server or production server
# if [ "$DJANGO_ENV" = "development" ]; then
#     echo "Running Django development server..."
#     python manage.py runserver 0.0.0.0:8000
# else
#     echo "Running Gunicorn production server..."
#     gunicorn oroshine_app.wsgi:application --bind 0.0.0.0:8000
fi





























# #!/bin/bash
# set -e

# echo "Waiting for database..."
# until nc -z -v -w30 "$PG_HOST" "$PG_PORT"
# do
#   echo "Waiting for database connection..."
#   sleep 2
# done
# echo "Database is up!"

# echo "Running Migrations..."
# python manage.py migrate --noinput
# echo "Migrations completed."

# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# echo "Starting Gunicorn server..."
# exec gunicorn oroshine_app.wsgi:application --bind 0.0.0.0:8000 --workers 4



# #!/bin/bash
# echo "Creating Migrations..."
# python manage.py makemigrations
# echo ====================================

# echo "Starting Migrations..."
# python manage.py migrate
# echo ====================================

# echo "Starting Server..."
# python manage.py runserver 0.0.0.0:8000
