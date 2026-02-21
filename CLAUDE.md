# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application for **argawaen.net**. Single-site architecture serving articles with categories, personal projects, DIY (bricolage) articles, network monitoring, user authentication and Markdown content. The project language (UI, comments, templates) is **French**. Timezone: Europe/Paris.

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

Database: PostgreSQL (service `db` dans Docker, volume `pgdata` pour la persistance). Variables d'environnement : `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

### Dépendances

- Django>=5.2,<5.3
- Pillow>=11.0
- django-markdownx>=4.0
- html5lib-truncation>=0.1
- gunicorn>=23.0
- celery[redis]>=5.4
- python-nmap>=0.7
- psycopg[binary]>=3.1

## Architecture

### URL Routing

`ROOT_URLCONF` is `multisite.urls`, which combines:
- `www.urls` — app-specific routes:
  - `/` — accueil (homepage, public)
  - `/a-propos/` — about page (public), with sub-pages `cv/` and `publications/`
  - `/mes-projets/` — projects (public, filtered by visibility level), with sub-routes `categorie/<slug>/` and `projet/<slug>/`
  - `/archives/` — archives main, `news/`, `research/` (requires `avance` level)
  - `/bricolage/` — DIY section (requires `avance` level), with detail `<slug>/`
  - `/monitoring/` — network monitoring (requires `administrateur` level), with sub-routes `machine/<id>/`, `machine/<id>/ping/` (SSE), `machine/<id>/ports/` (SSE), `serveur/<id>/`, `serveur/<id>/check/` (SSE)
  - `/administration/` — admin panel (requires `administrateur` level), sub-routes:
    - `utilisateurs/` — user management
    - `projets/` — CRUD for projects and categories
    - `bricolages/` — CRUD for DIY articles
    - `services/` — CRUD for machines, servers and service categories
- `connector.urls` — user auth & profile routes (under `profile/`): login, logout, register, password change/reset, profile view/edit
- `admin/` — Django admin
- `markdownx/` — Markdown editor support

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI, Celery config (`celery.py`)
  - **`connector/`** — User auth & profiles (login, register, password reset)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`), utilities, management commands
  - **`www/`** — Main website (articles, projects, bricolage, monitoring, custom widgets, template tags, context processors, Celery tasks)
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared base templates and registration templates
  - **`data/templates/www/`** — WWW app templates (including `widgets/` for custom form widgets)
  - **`data/static/`** — CSS, JS, images, fonts
  - **`data/media/`** — User uploads (avatars, article images, project icons, service icons)
- **`docker_data/`** — Docker runtime data (media, markdownx — not versioned)

### Docker

- **`Dockerfile`** — Image Python 3.12 avec nginx, gunicorn, nmap, iputils-ping et libpq-dev
- **`docker-compose.yml`** — Services `db` (PostgreSQL 16), `redis` (broker Celery) et `web` avec volumes pour media et pgdata
- **`entrypoint.sh`** — Attend PostgreSQL, lance migrate, collectstatic, nginx, celery worker, celery beat, puis gunicorn
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
- `BricolageArticle` — DIY article (`titre`, `slug`, `contenu` MarkdownxField, `date`), with `resume_md()` truncated to 200 chars
- `ServiceCategorie` — service/monitoring category (`nom`, `slug`, `mdi_icon_name`, `ordre`)
- `Machine` — network machine to monitor (`nom`/hostname, `categorie` FK, `adresse_ip`, `ip_statique`, `alerte_ip`, `ports_supplementaires`, `en_ligne`, `derniere_verification`, `derniere_vue_en_ligne`, `ports_ouverts` JSON, `dernier_scan_ports`). Validates IP in `RESEAU_LOCAL` (10.10.0.0/16). Methods: `hostname_complet()`, `resoudre_ip()`, `clean()`
- `Serveur` — web service to monitor (`titre`, `categorie` FK, `description`, `url`, `hostname`, `adresse`, `port`, `en_ligne`, `reverse_proxy_ok`, `derniere_verification`, `derniere_vue_en_ligne`). Multi-mode icon system like `Projet`. Methods: `has_icone()`, `icone_html()`, `lien()`, `adresse_effective()`, `clean()`. Requires at least `url` or `(adresse|hostname)+port`

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
- `BricolageArticleForm` — DIY article (auto-slug)
- `ServiceCategorieForm` — service category (auto-slug, auto-ordre)
- `MachineForm` — network machine (fields: `nom`, `categorie`, `ip_statique`, `ports_supplementaires`)
- `ServeurForm` — web service (validates single icon mode, validates url or address+port requirement, cleans unused icon fields)

`www/widgets.py`:
- `ColorPickerWidget` — HTML5 color picker with hex input (template: `www/widgets/color_picker.html`)
- `MdiIconPickerWidget` — icon selection grid with search from curated list of ~95 MDI icons (template: `www/widgets/mdi_icon_picker.html`)

### Celery & Background Tasks

`multisite/celery.py` — Celery app configuration with Django settings integration and auto-discovery of tasks.

`www/tasks.py` — Background monitoring tasks:
- `verifier_machines()` — shared task (runs every 300s): checks all machines via DNS resolution + ping, updates state
- `verifier_serveurs()` — shared task (runs every 300s): checks all servers via HTTP + TCP, updates state
- `scanner_ping(machine_id)` — SSE generator: resolves IP, pings machine, yields events
- `scanner_ports(machine_id)` — SSE generator: scans ports using nmap in chunks of 50, yields progress events
- `scanner_serveur(serveur_id)` — SSE generator: checks HTTP and TCP connectivity, yields status

Helper functions: `_ping()`, `_resoudre_et_mettre_a_jour()`, `_expand_ports()`, `_sse_event()`, `_verifier_url()`, `_verifier_tcp()`, `_check_serveur()`.

Default ports scanned: 27 common ports (21, 22, 23, 25, 53, 80, ...) + machine-specific `ports_supplementaires` field. Nmap timeout: 60s per chunk, 90s subprocess timeout.

Settings in `multisite/settings.py`:
```python
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULE = {
    "verifier-machines": {"task": "www.tasks.verifier_machines", "schedule": 300.0},
    "verifier-serveurs": {"task": "www.tasks.verifier_serveurs", "schedule": 300.0},
}
MONITORING_DOMAINE_DEFAUT = os.environ.get("MONITORING_DOMAINE_DEFAUT", "")
```

### Key Utilities

- **`www/render_utils.py`** — Page metadata, navigation structure, article filtering and pagination (10 articles/page). Navigation includes pages for accueil, à propos, mes projets, archives, bricolage (AVANCE), monitoring (ADMINISTRATEUR), administration (ADMINISTRATEUR). Admin subpages: utilisateurs, projets, bricolages, services
- **`www/context_processors.py`** — `navigation()` context processor adds `pages_left`, `pages_right`, `extpages`, `is_admin`, `user_level`, `user_level_display`, `user_is_avance` to all templates
- **`www/templatetags/template_extra.py`** — `pageSpecificBtn` filter for active navigation highlighting

### Tests

`www/tests.py` covers:
- `PagesAccessTest` — public pages return 200
- `ArchivesAccessTest` — archives/bricolage require avance level (anonymous→302, regular→403, avance→200)
- `TemplatesTest` — correct templates used (including bricolage and administration)
- `AdminUsersAccessTest` — user management access control and superuser protection
- `RemovedPagesTest` — old URLs return 404
- `ProjetsAccessTest` — project pages access, inactive project returns 404
- `ProjetsTemplatesTest` — correct templates for project pages
- `AdminProjetsAccessTest` — admin project CRUD access control and operations
- `ProjetIconeTest` — multi-mode icon system (MDI, URL, image, validation)
- `ProjetVisibiliteTest` — visibility filtering by user level (anonymous, registered, advanced, admin)
- `BricolageAccessTest` — bricolage pages access control (anonymous→302, regular→403, avance→200), detail and templates
- `AdminBricolagesAccessTest` — bricolage admin CRUD access control and operations (add, modify, delete)
- `MonitoringAccessTest` — monitoring page requires administrateur level (anonymous→302, regular→403, avance→403, admin→200)
- `AdminServicesAccessTest` — services admin CRUD for machines, servers and categories
- `MachineModelTest` — Machine model: __str__, IP validation in 10.10.0.0/16
- `ServeurModelTest` — Serveur model: icons, lien(), clean(), reverse_proxy, icon validation
- `MachineDetailAccessTest` — machine detail page and SSE endpoint access control
- `ScannerPingTest` — SSE ping generator: online/offline states
- `ScannerPortsTest` — SSE port scanner: chunked scanning, no-IP handling
- `ServeurDetailAccessTest` — server detail page and SSE endpoint access control
- `ServeurHostnameTest` — hostname support: creation, adresse_effective(), lien(), validation
- `ScannerServeurTest` — SSE server check: online/offline, hostname resolution
- `MachineHostnameTest` — hostname_complet(), DNS resolution, alerts for divergence and out-of-network IPs
- `MachineResolutionDnsTest` — DNS resolution in scanner_ping tasks
- `CeleryTasksTest` — verifier_machines and verifier_serveurs shared tasks (with mocked dependencies)
