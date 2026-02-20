# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application for **argawaen.net**. Single-site architecture serving articles with categories, user authentication and Markdown content. The project language (UI, comments, templates) is **French**. Timezone: Europe/Paris.

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

Nécessite `mysqlclient` (installé uniquement dans Docker) :

```bash
python manage.py import_from_mysql --host=192.168.5.1 --user=www_common --password=xxx --database=Site_Common
```

Database: SQLite (fichier `data/db/db.sqlite3`, monté via volume Docker pour la persistance).

### Dépendances

- Django>=5.2,<5.3
- Pillow>=11.0
- django-markdownx>=4.0
- html5lib-truncation>=0.1
- gunicorn>=23.0

## Architecture

### URL Routing

`ROOT_URLCONF` is `multisite.urls`, which combines:
- `www.urls` — app-specific routes:
  - `/` — accueil (homepage, public)
  - `/a-propos/` — about page (public), with sub-pages `cv/` and `publications/`
  - `/mes-projets/` — projects (public)
  - `/archives/` — archives main, `news/`, `research/` (requires `avance` level)
  - `/bricolage/` — DIY section (requires `avance` level)
  - `/administration/` — admin panel, `utilisateurs/` (requires `administrateur` level)
- `connector.urls` — user auth & profile routes (under `profile/`): login, logout, register, password change/reset, profile view/edit
- `admin/` — Django admin
- `markdownx/` — Markdown editor support

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI
  - **`connector/`** — User auth & profiles (login, register, password reset)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`), utilities, management commands
  - **`www/`** — Main website (articles with categories, template tags, context processors)
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared base templates and registration templates
  - **`data/templates/www/`** — WWW app templates
  - **`data/static/`** — CSS, JS, images, fonts
  - **`data/media/`** — User uploads (avatars, article images)
  - **`data/db/`** — SQLite database file
- **`docker_data/`** — Docker runtime data (db, media, markdownx — not versioned)

### Docker

- **`Dockerfile`** — Image Python 3.12 avec nginx et gunicorn
- **`docker-compose.yml`** — Service `web` avec volumes pour media et base SQLite
- **`entrypoint.sh`** — Crée le répertoire db, lance migrate, collectstatic, nginx, puis gunicorn
- **`nginx.conf`** — Reverse proxy (static/media servis directement, le reste vers gunicorn sur 127.0.0.1:8001)
- **`.env`** — Secrets et configuration (non versionné, copier `.env.example`)

### Models

`common/models.py` defines `SiteArticle` (with `MarkdownxField` for content, visibility flags, auto-sync in `save()`) and `SiteArticleComment` (requires moderation: `active=False` by default).

`www/models.py` defines:
- `Category` — article category (`nom`, `mdi_icon_name`)
- `SubCategory` — article sub-category (`nom`, `mdi_icon_name`)
- `Article` (extends `SiteArticle`) — adds `categorie` (FK) and `sous_categorie` (FK)
- `ArticleComment` (extends `SiteArticleComment`)

`connector/models.py` defines `UserProfile` (OneToOne with `User`, auto-created via `post_save` signal) with `avatar`, `birthDate`, and `user_level`.

### User Levels & Access Control

`connector/models.py` `UserProfile.user_level` is an integer field with 4 tiers:
- **0 — ENREGISTRE** (registered)
- **1 — AUTORISE** (authorized)
- **2 — AVANCE** (advanced)
- **3 — ADMINISTRATEUR** (administrator)

Helpers in `common/user_utils.py`: `get_user_level()`, `user_is_autorise()`, `user_is_avance()`, `user_is_administrateur()`. Legacy aliases `user_is_validated`, `user_is_developper`, `user_is_moderator` still exist.

Custom decorators in `www/views.py`: `@avance_required` (level >= 2), `@admin_required` (level >= 3).

### Article Visibility

Articles have 4 boolean flags: `private`, `superprivate`, `staff`, `developper`. Auto-sync in `SiteArticle.save()`:
- `staff` or `developper` → sets `private` and `superprivate`
- `superprivate` → sets `private`

Filtering logic in `www/render_utils.py`: `get_articles()`, `get_news_articles()`, `get_article()`.

### Key Utilities

- **`www/render_utils.py`** — Page metadata, navigation structure, article filtering and pagination (10 articles/page)
- **`www/context_processors.py`** — `navigation()` context processor adds `pages_left`, `pages_right`, `extpages`, `is_admin`, `user_level`, `user_level_display`, `user_is_avance` to all templates
- **`www/templatetags/template_extra.py`** — `pageSpecificBtn` filter for active navigation highlighting

### Tests

`www/tests.py` covers:
- `PagesAccessTest` — public pages return 200
- `ArchivesAccessTest` — archives/bricolage require avance level (anonymous→302, regular→403, avance→200)
- `TemplatesTest` — correct templates used
- `AdminUsersAccessTest` — user management access control and superuser protection
- `RemovedPagesTest` — old URLs return 404
