#!/bin/bash
set -e

# Appliquer les migrations
echo "Application des migrations..."
python /app/multisite/manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python /app/multisite/manage.py collectstatic --noinput

# Démarrer nginx
echo "Démarrage de nginx..."
nginx

# Démarrer celery worker
echo "Démarrage de celery worker..."
cd /app/multisite && celery -A multisite worker --loglevel=info --detach --pidfile=/tmp/celery-worker.pid

# Démarrer celery beat
echo "Démarrage de celery beat..."
cd /app/multisite && celery -A multisite beat --loglevel=info --detach --pidfile=/tmp/celery-beat.pid

# Démarrer gunicorn
echo "Démarrage de gunicorn..."
exec gunicorn \
    --chdir /app/multisite \
    --bind 127.0.0.1:8001 \
    --workers 3 \
    --threads 4 \
    --worker-class gthread \
    --timeout 150 \
    multisite.wsgi:application
