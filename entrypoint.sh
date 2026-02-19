#!/bin/bash
set -e

# Créer le répertoire de la base SQLite si nécessaire
mkdir -p /app/data/db

# Appliquer les migrations
echo "Application des migrations..."
python /app/multisite/manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python /app/multisite/manage.py collectstatic --noinput

# Démarrer nginx
echo "Démarrage de nginx..."
nginx

# Démarrer gunicorn
echo "Démarrage de gunicorn..."
exec gunicorn \
    --chdir /app/multisite \
    --bind 127.0.0.1:8001 \
    --workers 3 \
    multisite.wsgi:application
