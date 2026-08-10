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
#
# -Q celery,maintenance : sans la seconde file, les purges de la console ne sont
# jamais consommées. Deux files plutôt qu'une seule parce que kombu alterne entre
# elles, donc une purge publiée derrière un gros retard de checks obtient quand même
# son tour. Partager une file unique avait affamé cleanup_old_results pendant des mois
# et laissé la table des résultats atteindre 1,9 M de lignes.
#
# La file `network` n'est PAS ici : le scanner a besoin du réseau de l'hôte et de
# NET_RAW, ce qui n'a rien à faire dans le conteneur qui sert le site public. Il a son
# propre service dans docker-compose.yml.
echo "Démarrage de celery worker..."
cd /app/multisite && celery -A multisite worker -Q celery,maintenance --loglevel=info --detach --pidfile=/tmp/celery-worker.pid

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
