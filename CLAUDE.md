# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django multi-site web application for the **argawaen.net** domain. Uses a virtual host middleware to serve multiple sub-sites from a single Django project. The project language (UI, comments, templates) is **French**.

## Common Commands

All commands run from `/source/personnel/WebServer/multisite/`:

```bash
python manage.py runserver                # Dev server (localhost maps to potager app)
python manage.py test                     # Run all tests
python manage.py test <app_name>          # Run tests for a single app
python manage.py makemigrations           # Create migrations after model changes
python manage.py migrate                  # Apply migrations
python manage.py collectstatic            # Collect static files
```

Install dependencies:
```bash
python -m pip install Django Pillow mysqlclient django-markdownx html5lib-truncation
```

Database: MySQL on `192.168.5.1:3306`, default database `Site_Common`.

## Architecture

### Multi-Site via Virtual Hosts

`multisite/vhosts.py` contains `VHostMiddleware` which routes requests by hostname:

| Hostname | URL module | App |
|---|---|---|
| `www.argawaen.net` | `www.urls_base` | Main website |
| `drone.argawaen.net` | `drone.urls_base` | Drone project |
| `testsubject.argawaen.net` | `tsjt.urls_base` | Test Subject game |
| `ayoaron.argawaen.net` | `ayoaron.urls_base` | Ayoaron universe |
| `potager.argawaen.net` / `127.0.0.1` | `potager.urls_base` | Garden management |

Each app has a `urls_base.py` (includes admin, profile, markdownx routes) and a `urls.py` (app-specific routes).

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI, vhost middleware
  - **`connector/`** — User auth & profiles (shared across all sites)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`) and utilities
  - **`www/`** — Main website (articles with categories)
  - **`potager/`** — Garden management (plant tracking, garden grid 32×23, planting calendar)
  - **`drone/`** — Drone tracking (components, configurations, flights)
  - **`tsjt/`** — Test Subject game project articles
  - **`ayoaron/`** — Ayoaron universe articles
  - **`www_meteo/`** — Weather station
  - **`www_netadmin/`** — Network admin tools
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared base templates
  - **`data/templates/<app>/`** — Per-app templates
  - **`data/static/`** — CSS, JS, images, fonts
  - **`data/media/`** — User uploads (avatars, article images)

### Model Inheritance

`common/models.py` defines `SiteArticle` (with `MarkdownxField` for content) and `SiteArticleComment`. Apps extend these: `www.Article`, `drone.DroneArticle`, `tsjt.TSJTArticle`, `ayoaron.AyoaronArticle`.

### User & Permissions

`connector/` app provides a `UserProfile` model (OneToOne with Django's `User`). Permission groups: `validated`, `developper`, `moderator`. Article visibility levels: `private`, `superprivate`, `staff`, `developper` — checked via helpers in `common/user_utils.py`.

### Potager App Specifics

Most complex app. Uses a coordinate-based garden grid (32 rows × 23 cols). Key modules:
- `potager/potager.py` — Garden map logic (`get_potager_map()`, `get_potager_detail(row, col)`)
- Planting statuses: `READY`, `PLANNED`, `EN_GODET`, `EN_TERRE`, `RECOLTE`
- Stock statuses: `EN_STOCK`, `VIDE`, `EN_LIVRAISON`, `A_COMMANDER`, `BIENTOT_VIDE`
