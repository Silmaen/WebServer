# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django web application for **argawaen.net**. Single-site architecture serving articles with categories, user authentication and Markdown content. The project language (UI, comments, templates) is **French**.

## Common Commands

### Développement local (sans Docker)

All commands run from `/source/personnel/WebServer/multisite/`:

```bash
python manage.py runserver                # Dev server (localhost)
python manage.py test                     # Run all tests
python manage.py test <app_name>          # Run tests for a single app
python manage.py makemigrations           # Create migrations after model changes
python manage.py migrate                  # Apply migrations
python manage.py collectstatic            # Collect static files
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker

```bash
cp .env.example .env                      # Créer le fichier d'environnement (puis éditer)
docker compose up --build                 # Build et démarrage
docker compose up -d                      # Démarrage en arrière-plan
docker compose down                       # Arrêt
docker compose exec web python /app/multisite/manage.py test www   # Lancer les tests
docker compose exec web python /app/multisite/manage.py createsuperuser  # Créer un admin
docker compose logs -f web                # Suivre les logs
```

### Import de données depuis MySQL

Nécessite `mysqlclient` (`pip install mysqlclient`) :

```bash
python manage.py import_from_mysql --host=192.168.5.1 --user=www_common --password=xxx --database=Site_Common
```

Database: SQLite (fichier `data/db/db.sqlite3`, monté via volume Docker pour la persistance).

## Architecture

### URL Routing

`ROOT_URLCONF` is `multisite.urls`, which combines:
- `www.urls` — app-specific routes (articles, research, projects, links)
- `connector.urls` — user auth & profile routes (under `profile/`)
- `admin/` — Django admin
- `markdownx/` — Markdown editor support

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI
  - **`connector/`** — User auth & profiles (login, register, password reset)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`), utilities, management commands
  - **`www/`** — Main website (articles with categories, template tags)
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared base templates and registration templates
  - **`data/templates/www/`** — WWW app templates
  - **`data/static/`** — CSS, JS, images, fonts
  - **`data/media/`** — User uploads (avatars, article images)
  - **`data/db/`** — SQLite database file

### Docker

- **`Dockerfile`** — Image Python 3.12 avec nginx et gunicorn
- **`docker-compose.yml`** — Service `web` avec volumes pour media et base SQLite
- **`entrypoint.sh`** — Crée le répertoire db, lance migrate, collectstatic, nginx, puis gunicorn
- **`nginx.conf`** — Reverse proxy (static/media servis directement, le reste vers gunicorn)
- **`.env`** — Secrets et configuration (non versionné, copier `.env.example`)

### Model Inheritance

`common/models.py` defines `SiteArticle` (with `MarkdownxField` for content) and `SiteArticleComment`. The `www` app extends these with `Article` (adds `categorie`, `sous_categorie`) and `ArticleComment`.

### User & Permissions

`connector/` app provides a `UserProfile` model (OneToOne with Django's `User`, auto-created via signal). Permission groups: `validated`, `developper`, `moderator`. Article visibility levels: `private`, `superprivate`, `staff`, `developper` — checked via helpers in `common/user_utils.py`.
