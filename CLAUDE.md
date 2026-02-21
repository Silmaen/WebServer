# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application for **argawaen.net**. Single-site architecture serving articles with categories, personal projects, user authentication and Markdown content. The project language (UI, comments, templates) is **French**. Timezone: Europe/Paris.

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
  - `/mes-projets/` — projects (public, filtered by visibility level), with sub-routes `categorie/<slug>/` and `projet/<slug>/`
  - `/archives/` — archives main, `news/`, `research/` (requires `avance` level)
  - `/bricolage/` — DIY section (requires `avance` level)
  - `/administration/` — admin panel (requires `administrateur` level), sub-routes: `utilisateurs/`, `projets/` (CRUD for projects and categories)
- `connector.urls` — user auth & profile routes (under `profile/`): login, logout, register, password change/reset, profile view/edit
- `admin/` — Django admin
- `markdownx/` — Markdown editor support

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI
  - **`connector/`** — User auth & profiles (login, register, password reset)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`), utilities, management commands
  - **`www/`** — Main website (articles, projects, custom widgets, template tags, context processors)
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared base templates and registration templates
  - **`data/templates/www/`** — WWW app templates (including `widgets/` for custom form widgets)
  - **`data/static/`** — CSS, JS, images, fonts
  - **`data/media/`** — User uploads (avatars, article images, project icons)
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
- `ProjetCategorie` — project category (`nom`, `slug`, `mdi_icon_name`, `ordre`)
- `Projet` — personal project (`titre`, `slug`, `categorie` FK, `resume`, `contenu` MarkdownxField, `lien_externe`, `couleur`, `date_creation`, `actif`, `visibilite`, `ordre`) with multi-mode icon system (`mdi_icon_name`, `icone_image`, `icone_url` — only one active at a time)

`connector/models.py` defines `UserProfile` (OneToOne with `User`, auto-created via `post_save` signal) with `avatar`, `birthDate`, and `user_level`.

### User Levels & Access Control

`connector/models.py` `UserProfile.user_level` is an integer field with 4 tiers:
- **0 — ENREGISTRE** (registered)
- **1 — AUTORISE** (authorized)
- **2 — AVANCE** (advanced)
- **3 — ADMINISTRATEUR** (administrator)

`get_user_level()` returns **-1** for anonymous (unauthenticated) users.

Helpers in `common/user_utils.py`: `get_user_level()`, `user_is_autorise()`, `user_is_avance()`, `user_is_administrateur()`. Legacy aliases `user_is_validated`, `user_is_developper`, `user_is_moderator` still exist.

Custom decorators in `www/views.py`: `@avance_required` (level >= 2), `@admin_required` (level >= 3).

### Article Visibility

Articles have 4 boolean flags: `private`, `superprivate`, `staff`, `developper`. Auto-sync in `SiteArticle.save()`:
- `staff` or `developper` → sets `private` and `superprivate`
- `superprivate` → sets `private`

Filtering logic in `www/render_utils.py`: `get_articles()`, `get_news_articles()`, `get_article()`.

### Project Visibility

Projects use a single integer field `visibilite` (default=-1) indicating the minimum user level required:
- **-1** — Public (visible to anonymous)
- **0** — Enregistré
- **1** — Autorisé
- **2** — Avancé
- **3** — Administrateur

Choices defined in `VISIBILITE_CHOICES` constant in `www/models.py`. Filtering in the 3 public views (`mes_projets`, `mes_projets_categorie`, `mes_projets_detail`) uses `visibilite__lte=get_user_level(request.user)`. Admin views show all projects regardless of visibility.

### Forms & Widgets

`www/forms.py`:
- `ArticleCommentForm` — comment creation (field: `contenu`)
- `ProjetCategorieForm` — project category (auto-slug, auto-ordre)
- `ProjetForm` — project (auto-slug, auto-ordre, validates single icon mode, cleans unused icon fields)

`www/widgets.py`:
- `ColorPickerWidget` — HTML5 color picker with hex input (template: `www/widgets/color_picker.html`)
- `MdiIconPickerWidget` — icon selection grid with search from curated list of ~95 MDI icons (template: `www/widgets/mdi_icon_picker.html`)

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
- `ProjetsAccessTest` — project pages access, inactive project returns 404
- `ProjetsTemplatesTest` — correct templates for project pages
- `AdminProjetsAccessTest` — admin project CRUD access control and operations
- `ProjetIconeTest` — multi-mode icon system (MDI, URL, image, validation)
- `ProjetVisibiliteTest` — visibility filtering by user level (anonymous, registered, advanced, admin)
