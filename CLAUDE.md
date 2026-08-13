# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 web application for **argawaen.net**. Single-site architecture serving articles with categories, personal projects, DIY (bricolage) articles, network monitoring, user authentication and Markdown content. The project language (UI, comments, templates) is **French**. Timezone: Europe/Paris.

The repository is the result of a merge between the personal site (`www`, `common`, `connector`) and a homelab network-monitoring application, now **la console**, living under `multisite/apps/` and served under `/console/`. The two halves share one look: console pages extend `www/base.html` and get their title and inline sub-navigation from `apps.core.mixins.ConsolePageMixin`, exactly as `www` pages get theirs from `www.render_utils.get_page_data`. There is no second theme and no Bootstrap bundle — `data/static/console/css/console.css` only maps the Bootstrap class names inherited templates still use onto the site's CSS variables.

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

`deploy.sh` at the repository root is the all-in-one entry point (its user-facing text is
in English, unlike the rest of the project). It checks the tooling and `.env`, warns on a
missing inventory file, pre-creates the media directory with the right owner, updates the
repository, refreshes the images, builds, starts, and waits for `db`, `redis` and `web` to
report healthy.

`pull_images()` exists because a pinned tag never moves on its own: without it
`postgres:16-alpine` and `redis:7-alpine` stay on the image pulled at the first deployment,
so the minor releases — which is where the security fixes are — never land. It refreshes the
registry-only services with `docker compose pull --ignore-buildable`, then the Dockerfile's
`FROM` separately (a buildable service is skipped by that command, and a stale base image is
just as bad), reading the tag from the Dockerfile rather than repeating it. A registry it
cannot reach is a **warning, not a failure**: the images already on disk are enough to
deploy, and aborting would leave the update half done.

```bash
./deploy.sh                 # déploiement complet : pull + build + up + attente
./deploy.sh --no-pull       # ne rien récupérer : ni le dépôt, ni les images
                            #   (obligatoire si l'arbre est sale)
./deploy.sh --tests         # lance la suite de tests avant de démarrer
./deploy.sh --dry-run       # affiche le plan sans rien exécuter
./deploy.sh check           # vérifie seulement s'il y a une mise à jour, ne change rien
./deploy.sh status | logs | stop | restart
./deploy.sh tests [app]     # tests dans un conteneur jetable, base de test dédiée
./deploy.sh superuser       # créer un admin
./deploy.sh shell           # shell Django
```

Les commandes sous-jacentes, si besoin :

```bash
cp .env.example .env                      # Créer le fichier d'environnement (puis éditer)
docker compose up --build                 # Build et démarrage
docker compose down                       # Arrêt
docker compose exec web python /app/multisite/manage.py test www   # Lancer les tests
docker compose logs -f web                # Suivre les logs
```

`./deploy.sh check` (alias `--check`) ne fait qu'un `git fetch` et compare à l'upstream :
il ne construit rien, ne démarre rien, et n'écrit que les refs de suivi. Ses codes de
retour sont faits pour être scriptés (cron, supervision) : **0** à jour, **10** mise à
jour en attente, **1** impossible de conclure (pas un dépôt, pas d'upstream, fetch
échoué).

Migrations et `collectstatic` sont lancés par `entrypoint.sh` au démarrage du conteneur
`web` : ni `deploy.sh` ni toi n'avez à les rejouer à la main.

### Import de données depuis MySQL

Nécessite `pymysql` :

```bash
python manage.py import_from_mysql --host=192.168.5.1 --user=www_common --password=xxx --database=Site_Common
```

### Migration de données

```bash
# Export des données (depuis la base actuelle)
python manage.py migrate_to_postgres -o dump.json

# Import dans PostgreSQL (après configuration)
python manage.py migrate
python manage.py loaddata dump.json
```

Database: PostgreSQL (service `db` dans Docker, bind mount `docker_data/db` pour la persistance). Variables d'environnement : `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

### Dépendances

Site: `Django>=5.2,<5.3`, `Pillow`, `django-markdownx`, `html5lib-truncation`, `gunicorn`, `celery[redis]`, `python-nmap`, `psycopg[binary]`, `Pygments`, `pymdown-extensions`.

Arrived with the console: `djangorestframework`, `django-filter`, `django-htmx`, `django-celery-beat`, `mozilla-django-oidc`, `scapy`, `dnspython`, `requests`, `redis`.

Front-end: no framework. **Bootstrap is not loaded** (neither CSS nor JS) — see "Console styling" below. Material Design Icons comes from a CDN in `www/base.html`; Chart.js and htmx are loaded only by the pages that need them, in their own `extra_js`.

## Architecture

### URL Routing

`ROOT_URLCONF` is `multisite.urls`, which combines:
- `/` — **dispatches** through `www.views_home.home` rather than serving a single page: a guest gets `a_propos`, an `administrateur` session gets `monitoring` (called, not redirected, so the address stays `/`), a `viewers`/`admins` group member is redirected to `fleet:index`. `path('', home)` sits **before** `www_patterns`, so it wins at `''` and the `accueil` view is only reachable by name through `reverse('accueil')`.
- `www.urls` — app-specific routes:
  - `/a-propos/` — about page (public), with sub-pages `cv/` and `publications/`
  - `/mes-projets/` — projects (public, filtered by visibility level), with sub-routes `categorie/<slug>/` and `projet/<slug>/`
  - `/archives/` — archives main, `news/`, `research/` (requires `avance` level)
  - `/bricolage/` — DIY section (requires `avance` level), with detail `<slug>/`
  - `/monitoring/` — machine monitoring (requires `administrateur` level). **Machines and services are two pages**, joined by the inline sub-navigation: `/monitoring/` (machines) and `/monitoring/services/` (web services). Detail and SSE sub-routes: `machine/<id>/`, `machine/<id>/ping/` (SSE), `machine/<id>/ports/` (SSE), `serveur/<id>/`, `serveur/<id>/check/` (SSE)
  - `/administration/` — admin panel (requires `administrateur` level), sub-routes:
    - `utilisateurs/` — user management
    - `projets/` — CRUD for projects and categories
    - `bricolages/` — CRUD for DIY articles
    - `services/` — CRUD for machines, servers and service categories
- `connector.urls` — user auth & profile routes (under `profile/`): login, logout, register, password change/reset, profile view/edit
- `/console/` — la console (see below), from `multisite/apps/`:
  - `/console/` — dashboard (`apps.dashboard`)
  - `/console/fleet/` — declared machines, and `/console/fleet/stacks/` — deployed compose stacks. **Two pages**, joined by an inline Machines / Stacks sub-navigation; both read the same assembled state. `POST fleet/approve/<machine>/<verb>/` and `POST fleet/deploy/<machine>/<project>/` publish an ntfy approval (staff only, see the ntfy contract below); `POST fleet/stacks/<uuid>/oublier/` and `POST fleet/stacks/oublier-disparues/` forget stacks no machine reports any more (staff only, see "A stack that moves or disappears")
  - `/console/devices/` — devices observed by the scanner, with `add/`, `<uuid>/`, `<uuid>/edit/`, `<uuid>/delete/`, `<uuid>/probe/`
  - `/console/networks/` — monitored networks and gateway credentials
  - `/console/monitoring/` — supervision history (time series + state transitions)
  - `/console/admin-panel/`, `/console/tasks/`, `/console/tasks/<uuid>/` — console administration and background-task tracking
- `/api/fleet/` — bearer-token endpoints the machines POST reports to (outside the DRF session defaults: a shell script on a timer cannot follow an SSO redirect)
- `/api/` — internal JSON API (`apps.api`): health check, monitoring time series, device list
- `/oidc/` — SSO through authentik, plus `/oidc/silent/` for the silent-auth middleware
- `admin/` — Django admin
- `markdownx/` — Markdown editor support

### Directory Structure

- **`multisite/`** — Django project root (contains `manage.py`)
  - **`multisite/`** — Project settings, URL config, WSGI/ASGI, Celery config (`celery.py`)
  - **`connector/`** — User auth & profiles (login, register, password reset)
  - **`common/`** — Base models (`SiteArticle`, `SiteArticleComment`), utilities, management commands
  - **`www/`** — Main website (articles, projects, bricolage, monitoring, custom widgets, template tags, context processors, Celery tasks)
  - **`apps/`** — la console. The `apps.` prefix is deliberate: it preserves the migration app labels, so the existing database carries over instead of being rebuilt.
    - **`apps/core/`** — cross-cutting: `TimeStampedModel`, `BackgroundTask`, access mixins, `ConsolePageMixin`, OIDC backend (`auth.py`), silent SSO (`sso.py`), console-scoped 403 middleware, task logger
    - **`apps/fleet/`** — declared machines (mirror of `_common/inventory.conf`), their reports, deployed stacks, wud image lag, ntfy approvals, and `enrich.py` which grafts all of it onto `www`'s monitoring page
    - **`apps/devices/`** — devices observed on the network, port scans, OS probes
    - **`apps/network/`** — monitored networks, OpenWrt gateway credentials and ubus queries, discovery tasks
    - **`apps/monitoring/`** — availability checks and their results, `history.py` (state transitions), `policy.py` (which targets belong to gatus rather than here)
    - **`apps/dashboard/`** — console overview page
    - **`apps/api/`** — internal JSON API (views in `views.py`, routes only in `urls.py`)
- **`data/`** — Static files, media uploads, and templates
  - **`data/templates/common/`** — Shared registration templates
  - **`data/templates/www/`** — WWW app templates (including `widgets/` for custom form widgets)
  - **`data/templates/console/`** — Console templates. `base.html` plugs them into `www/base.html`; `includes/pagination.html` is the single paginator used by every console list
  - **`data/static/`** — CSS, JS, images, fonts (`console/css/console.css`, `console/js/` for the two extracted scripts)
  - **`data/media/`** — User uploads (avatars, article images, project icons, service icons)
- **`docker_data/`** — Docker runtime data (db, media — not versioned)

`TEMPLATES["DIRS"]` lists `data/templates/console` as a root, so console templates reference each other without a prefix (`base.html`, `fleet/index.html`).

### Docker

- **`Dockerfile`** — Image Python 3.12 avec nginx, gunicorn, nmap, iputils-ping, libpq-dev et curl
- **`docker-compose.yml`** — Services `db` (PostgreSQL 16), `redis` (broker Celery), `web`, et `celery_scanner` — le seul service privilégié : scanner le LAN demande `network_mode: host` et `NET_RAW`, ce qui n'a rien à faire dans le conteneur qui sert le site public. Il ne consomme que la file `network`. `db` et `redis` sont exposés sur la loopback parce que, depuis le namespace réseau de l'hôte, le nom `db` ne résout pas. `web` monte aussi `_common/inventory.conf` en lecture seule (`INVENTORY_FILE`) : `apps.fleet` le reflète sans jamais l'écrire
- **`entrypoint.sh`** — Lance migrate, collectstatic, nginx, celery worker, celery beat, puis gunicorn
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
- `Machine` — network machine to monitor (`nom`/hostname, `categorie` FK, `adresse_ip`, `ip_statique`, `alerte_ip`, `ports_supplementaires`, `en_ligne`, `derniere_verification`, `derniere_vue_en_ligne`, `ports_ouverts` JSON, `dernier_scan_ports`). Validates IP in `RESEAUX_LOCAUX` (10.10.0.0/16 principal, 10.8.0.0/16 guest, 10.9.0.0/16 IoT, 10.0.0.0/24 routeur↔box) via `ip_dans_reseaux_locaux()`. Methods: `hostname_complet()`, `resoudre_ip()`, `clean()`
- `Serveur` — web service to monitor (`titre`, `categorie` FK, `description`, `url`, `hostname`, `adresse`, `port`, `en_ligne`, `reverse_proxy_ok`, `derniere_verification`, `derniere_vue_en_ligne`). Multi-mode icon system like `Projet`. Methods: `has_icone()`, `icone_html()`, `lien()`, `adresse_effective()`, `clean()`. Requires at least `url` or `(adresse|hostname)+port`

`connector/models.py` defines `UserProfile` (OneToOne with `User`, auto-created via `post_save` signal) with `avatar`, `birthDate`, and `user_level`. `UserProfile.save()` derives `User.is_staff` from `user_level` — one direction only, so a test that needs a staff user must set `user_level`, not `is_staff`.

Console models (`multisite/apps/*/models.py`):
- `apps.core` — `TimeStampedModel` (abstract: UUID pk + timestamps), `BackgroundTask` (Celery task tracking with log, result, `triggered_by`)
- `apps.fleet` — `Machine` (**declared**, mirror of `_common/inventory.conf`), `Report` (a `homelab-report` document, kept as history), `Stack` (a deployed compose project as the Docker daemon reports it, with a `severity` for missing/untracked compose files and a `present` flag saying whether the last report still mentions it)
- `apps.devices` — `Device` (**observed** by the scanner), `DevicePort`, `ConnectionLog`
- `apps.network` — `Network` (CIDR, scan interval), `GatewayCredential` (OpenWrt ubus access)
- `apps.monitoring` — `MonitoringCheck` (ICMP/TCP/HTTP/DNS on a device), `CheckResult`

`fleet.Machine` and `devices.Device` are deliberately **not** merged: one is declared, the other observed, and the gap between them is the interesting signal. Same for the two check engines — gatus owns declared machines and services, `apps.monitoring` owns everything else the scanner finds (`apps/monitoring/policy.py`).

### Acting on a machine: the ntfy contract

`apps/fleet/ntfy.py` is the **only** way the console affects a machine, and its invariant is that **no command is ever transmitted**. The console publishes a verb plus names it has first validated against the database, on an ntfy topic it can write but not read; the machine's own agent decides which playbook or script that means. The worst an attacker reaching these endpoints can obtain is asking a machine to converge on what its git repository already describes.

Two shapes exist:
- **Per machine** — `publish(verb, machine)` writes `<verb> <machine>`, `verb` one of `VERBS` (`converge`, `upgrade`, `upgrade-reboot`, `report`). Buttons on the Fleet page.
- **Per stack** — `publish_deploy(machine, project)` writes `deploy <machine> <project>`, two names and never a path. Button on the Stacks page, shown only when the stack is `deployable`.

**`Stack.deployable` requires `homelab-probe` to report a deploy script.** The probe adds a `deploy` key to the stack entry of the report:

```json
{"project": "immich", "path": "/srv/stacks/immich", "compose": "tracked",
 "behind": 2, "deploy": "deploy.sh"}
```

Ingestion is deliberately tolerant (`apps/fleet/ingest.py` `_deploy_script`): a probe that does not know the field sends nothing and the stack simply is not deployable; `-` means "no script"; and only a bare filename is accepted — a path comes from the machine and is never trusted. A stack whose compose file has disappeared is never deployable, since the script could not run anyway.

So the feature spans two repositories. **In this one** everything is in place: field, ingestion, columns, button, guards, tests. **In `home-server-stacks`** two things are still needed: `homelab-probe` must emit `deploy`, and the agent must handle the `deploy <machine> <project>` message by locating and running that stack's script.

### Is a stack out of date?

Two independent signals, deliberately kept apart on the Stacks page because they have different remedies:
- **git** — `Stack.behind` (commits behind the remote) and `Stack.git_en_retard`. `None` when the probe cannot tell, which is not the same as zero. A commit never applied means "redeploy".
- **images** — wud sees a newer tag. `apps/fleet/wud.py` `by_container()` returns every watched container per machine, and `apps/fleet/state.py` `_attacher_images()` maps them onto stacks: by the `com.docker.compose.project` label when wud exposes it, otherwise by container-name prefix, longest project first (a service name can contain hyphens, and two projects can share a prefix). Each stack gets an in-memory `.images` dict, like `enrich.annotate` does with `.flotte`.

**A wud signal is only worth as much as the labels feeding it.** Unconstrained, wud takes the "greatest" tag of a repository, which made it announce `postgres:16-alpine` → `19beta2-trixie` and `redis:*-alpine` → `32bit-stretch`: a beta, a foreign variant, and a column that cries wolf. So `docker-compose.yml` carries, per service:

- `wud.tag.include` on the images pulled from a registry, anchored on the **current major** (`'^16-alpine$$'`, `'^8-alpine$$'`). Note the `$$`: compose interpolates `$`, so a single one would corrupt the regex. Bumping the image tag means bumping this regex on the same line of thought — which is precisely when the question deserves to be asked.
- `wud.watch: 'false'` on `web` and `celery_scanner`, built here and therefore present in no registry: wud was looking up `library/webserver-web:latest` on Docker Hub and reporting a 401 per container. What those images really track is the Dockerfile's base, which `deploy.sh` pulls at every deployment.

The other stacks of the lab carry no wud label at all, so the same noise is on them (`authentik-postgresql`, `pretloc-db-1`, `sensor_server-redis-1`, the `nginx` containers, plus a 401 on every locally built image). Fixing it belongs to `home-server-stacks`, with these same two labels.

### A stack that moves or disappears

`homelab-probe` derives the stack list from what the Docker daemon declares, so **the reported list is complete for that machine**: what is not in it is not deployed any more. `apps/fleet/ingest.py` `_store_stacks()` reconciles on that basis and sets `Stack.present = False` on the rest.

Nothing is deleted by ingestion — "this was deployed here" is information — but `present` is what separates a **broken** stack from a **gone** one, and that distinction is the whole point. Without it, moving or removing a stack left a row frozen on the last state the probe saw, which is the state mid-move: `compose: missing`. The page then announced "stack without a usable compose file" **for ever**, and no gesture could fix it — the only machine able to update that row no longer knew it. So:

- `Stack.severity` and `Stack.deployable` are empty/false when `present` is false. The red alert on both fleet pages, and the badge on `www`'s monitoring page, only count reported stacks.
- The Stacks page still lists them, greyed (`.stack-absente`), with a "plus déployée" badge and — for staff — `POST fleet/stacks/<uuid>/oublier/` to forget the row, plus `POST fleet/stacks/oublier-disparues/` to sweep them all. This is the only delete in the whole console, and it only touches this database.
- A stack still reported is **refused** by the forget view: deleting it would achieve nothing, the next report would recreate it and lose its `first_seen`.
- A probe that sends **no** `stacks` key reconciles nothing. "No stacks" and "I don't talk about stacks" are two different documents, and confusing them would mark a whole machine as having nothing deployed.
- `ntfy.publish_deploy()` and `DeployStackView` filter on `present=True`: a moved stack leaves a row with the same project name, and the one to deploy is the one still running.

### User Levels & Access Control

`connector/models.py` `UserProfile.user_level` is an integer field with 4 tiers:
- **0 — ENREGISTRE** (registered)
- **1 — AUTORISE** (authorized)
- **2 — AVANCE** (advanced)
- **3 — ADMINISTRATEUR** (administrator)

`get_user_level()` returns **-1** for anonymous (unauthenticated) users.

Helpers in `common/user_utils.py`: `get_user_level()`, `user_is_autorise()`, `user_is_avance()`, `user_is_administrateur()`. Legacy aliases `user_is_validated`, `user_is_developper`, `user_is_moderator` still exist.

Custom decorators in `www/views.py`: `@avance_required` (level >= 2), `@admin_required` (level >= 3).

The console uses a **second, independent** scale: Django groups. `apps/core/mixins.py` provides `ViewerRequiredMixin` (group `viewers` or `admins`, or staff) for read pages and `StaffRequiredMixin` (`is_staff`) for write pages. `apps/core/auth.py` maps authentik's groups (`OIDC_ADMIN_GROUP`, `OIDC_VIEWER_GROUP`) onto those Django groups **and** onto `userprofile.user_level`, so one authentik account satisfies both scales.

`apps/core/middleware.py` `InactiveUserMiddleware` renders the honest 403 page (`console/core/forbidden.html`) instead of redirecting to a login already passed. It is **scoped to `/console/` on purpose**: an unscoped version locked every ordinary logged-in member out of the public site, including their own profile.

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

`www/forms.py` — two mixins carry what was duplicated between forms: `AutoSlugOrdreMixin` (auto-slug + auto-ordre) and `IconeModeMixin` (validates a single active icon mode, cleans the unused icon fields).
- `ArticleCommentForm` — comment creation (field: `contenu`)
- `ProjetCategorieForm` — project category (`AutoSlugOrdreMixin`)
- `ProjetForm` — project (`AutoSlugOrdreMixin` + `IconeModeMixin`)
- `BricolageArticleForm` — DIY article (auto-slug)
- `ServiceCategorieForm` — service category (`AutoSlugOrdreMixin`)
- `MachineForm` — network machine (fields: `nom`, `categorie`, `ip_statique`, `ports_supplementaires`)
- `ServeurForm` — web service (`IconeModeMixin`, plus validates url or address+port)

`www/models.py` `IconeMixin` (plain Python class, `ICONE_CSS_CLASS` attribute) carries `has_icone()` / `icone_html()` for both `Projet` and `Serveur`.

The 6 families of admin views (`admin_projet_*`, `admin_projet_categorie_*`, `admin_bricolage_*`, `admin_machine_*`, `admin_serveur_*`, `admin_service_categorie_*`) all go through two helpers in `www/views.py`: `_rendre_formulaire()` and `_supprimer()`. The individual view names are unchanged — URLs and tests reference them.

`www/widgets.py`:
- `ColorPickerWidget` — HTML5 color picker with hex input (template: `www/widgets/color_picker.html`)
- `MdiIconPickerWidget` — icon selection grid with search from curated list of ~95 MDI icons (template: `www/widgets/mdi_icon_picker.html`)

### Celery & Background Tasks

`multisite/celery.py` — Celery app configuration with Django settings integration and auto-discovery of tasks.

`www/tasks.py` — Background monitoring tasks. `verifier_machines()` and `verifier_serveurs()` are **no longer scheduled** (one check engine only: `apps.monitoring`); the functions stay because the module also carries the SSE generators the views call on demand.
- `verifier_machines()` — shared task: checks all machines via DNS resolution + ping, updates state
- `verifier_serveurs()` — shared task: checks all servers via HTTP + TCP, updates state
- `scanner_ping(machine_id)` — SSE generator: resolves IP, pings machine, yields events
- `scanner_ports(machine_id)` — SSE generator: scans ports using nmap in chunks of 50, yields progress events
- `scanner_serveur(serveur_id)` — SSE generator: checks HTTP and TCP connectivity, yields status

Helper functions: `_ping()`, `_resoudre_et_mettre_a_jour()`, `_expand_ports()`, `_sse_event()`, `_verifier_url()`, `_verifier_tcp()`, `_check_serveur()`.

Default ports scanned: 27 common ports (21, 22, 23, 25, 53, 80, ...) + machine-specific `ports_supplementaires` field. Nmap timeout: 60s per chunk, 90s subprocess timeout.

Console tasks: `apps.monitoring.tasks` (`schedule_due_checks` every 15s, `execute_check`, `cleanup_old_results`), `apps.network.tasks` (`schedule_due_scans`, `gateway_scan_task`, `quick_scan_task`, `discover_network_task` — all three built on the same `_traiter_hotes` helpers), `apps.devices.tasks` (`schedule_device_probes`, `quick_probe_task`, `deep_probe_task`), `apps.fleet.tasks` (`cleanup_old_reports`).

Two queues: `network` for anything needing the host network namespace and `NET_RAW` (its own privileged `celery_scanner` service in compose), and `maintenance` consumed alongside `celery` so a purge always gets its turn.

Settings in `multisite/settings.py`: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_TASK_ROUTES` (routes `apps.network.*` and `apps.devices.tasks.*` to the `network` queue), `CELERY_BEAT_SCHEDULE`, `MONITORING_DOMAINE_DEFAUT`, and the `OIDC_*` block (`OIDC_ENABLED` is simply "`OIDC_RP_CLIENT_ID` is set").

### Markdown Rendering

Markdown is rendered via `django-markdownx` using `markdownify()` from `markdownx.utils`. Extensions configured in `MARKDOWNX_MARKDOWN_EXTENSIONS`:
- `markdown.extensions.extra` — tables, fenced code, footnotes, abbreviations, attr_list, def_list
- `markdown.extensions.codehilite` — syntax highlighting via Pygments (theme monokai, `guess_lang: True`)
- `pymdownx.tasklist` — GitHub-style task lists (`- [ ]` / `- [x]`) with custom checkboxes

CSS: all markdown output containers use the `.markdown-body` class (added in templates), which restores standard HTML styling (headings bold with margins, list bullets, blockquote borders, code blocks, tables). Pygments monokai theme colors are scoped under `.markdown-body .codehilite`. Task list checkboxes styled under `.markdown-body .task-list-control`.

### Page layout & console styling

One layout for the whole application. Every content page — `www` and console alike — renders:

```django
{% block content %}
<div class="static-page">      {# la console ajoute la classe `console` #}
    <h2>Titre de la page</h2>
    …
</div>
{% endblock %}
```

The `.PageTitle` banner is only used by the article pages (`baseWithArticles.html`), which do not override `content`. Console pages never write their own `<h1>`: `console/base.html` renders `<h2>{{ page_subtitle }}</h2>`, and `page_subtitle` comes from `ConsolePageMixin`. A console page therefore declares `page_title`, `nav_page`, `subpage_title` and `subpages` on its view, never a title in the template.

Shared building blocks, all defined in CSS and never inline:
- `.console-toolbar` / `-info` / `-actions` — the row under a page title: context on the left, buttons on the right. `www/machine_detail.html` and `serveur_detail.html` use `.machine-scan-header` / `.machine-scan-actions`, which share the same rules.
- `.console-filters` — filter row above a table; the submit button lines up with the fields via `--field-height`.
- `.console-empty` — the muted centred message of an empty table.
- `.console-info-table` — key/value tables; the label column width is on the class, not on each `<th>`.
- `.pagination` / `.page-item` / `.page-link` — horizontal, via the single `console/includes/pagination.html` partial. It uses `{% querystring %}` (Django 5.1+) so the current filters survive a page change.
- `.btn-group.btn-group-sm` — wraps the buttons of an "Actions" cell; `> form { display: contents }` keeps a `<form>`-wrapped button aligned with an `<a>`.
- `.is-hidden` — the generic "hidden" state class that JavaScript toggles. **Never** assign `element.style.display` from JS.
- `.col-secondaire` — **column priority**, the answer to lists carrying 5 to 11 columns. Under 768 px the marked columns disappear and only identity, state and actions remain; the rest is one tap away on the object's own page. The class goes on the `<th>` **and** on its `<td>` — it is the pair that removes a column, so a table whose rows are built in JavaScript needs it in the JS too (`console/js/monitoring_dashboard.js`). Two consequences are handled by CSS, not by each template: a table that hides columns no longer needs to scroll (`min-width: 0` via `:has(.col-secondaire)`), and its actions cell lets its buttons wrap instead of staying on one line — the opposite of the wide-screen arbitration, which chose to scroll the table instead.

**Bootstrap is gone but its class names remain** in templates inherited from network_monitor. `console.css` maps the ones actually used onto the site's CSS variables. Consequences worth knowing before touching those pages:
- No Bootstrap JS. Dropdowns are native `<details>`/`<summary>` (`.console-dropdown`), and there are no tabs left — the console admin page is three stacked `.monitoring-section` blocks. Never reintroduce `data-bs-*`.
- No colour literals outside `:root`, and no `style="..."` for static styling. The one tolerated exception is a dynamic custom property (`style="--progress: 87%"`).
- Chart colours are read from the theme with `getComputedStyle`, so `--green`, `--yellow`, `--red`, `--text`, `--text-secondary`, `--bg-surface` and `--border` must stay 6-digit hex.
- Messages are rendered once, by `www/base.html`. Do not add a message block to a console page.

### Key Utilities

- **`www/render_utils.py`** — Page metadata, navigation structure, article filtering and pagination (10 articles/page). **It is the single place that describes every menu in the application**, console entries included: accueil, à propos, mes projets, archives (AVANCE), bricolage (AVANCE), monitoring (ADMINISTRATEUR), flotte (AUTORISE), appareils (AUTORISE), réseaux (ADMINISTRATEUR), administration (ADMINISTRATEUR). Inline sub-navigations: `a_propos_subpages`, `archives_subpages`, `monitoring_subpages` (Machines / Services), `fleet_subpages` (Machines / Stacks), `admin_subpages`
- **`www/context_processors.py`** — `navigation()` context processor adds `pages_left`, `pages_right`, `extpages`, `is_admin`, `user_level`, `user_level_display`, `user_is_avance` to all templates
- **`apps/core/context_processors.py`** — `sso()` adds `oidc_enabled`, `oidc_admin_group`, `oidc_viewer_group`
- **`apps/core/mixins.py`** — `ConsolePageMixin` supplies `page_subtitle`, `page`, `subpage`, `subpages` to console pages; override `get_page_title()` when the title depends on the object
- **`apps/monitoring/history.py`** — `transitions()` / `transitions_par_appareil()`, the single implementation of state-change detection (used by the API, the device detail page and the dashboard)
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
- `MachineModelTest` — Machine model: __str__, IP validation across all local networks (principal, guest, IoT, routeur)
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
- `MonitoringServicesAccessTest` — the services page, split off from the machines page: access control, template, active sub-page
- `TemplatesTest` also asserts what `/` dispatches to (guest → `a_propos`, admin → `monitoring`)

`apps/fleet/tests.py` covers the fleet:
- `IngestDeployScriptTest` — the report's `deploy` field: reported, absent, `-`, a path (refused), and a missing compose file
- `RetardStackTest` — the two lags kept apart, and image-to-stack attribution by compose label then by name prefix
- `WudGroupementTest` — `local` watcher means selene, per-machine summary, project read from labels
- `PublicationDeploiementTest` — `publish_deploy` validates machine, stack, script and token **before** publishing, and the body is `deploy <machine> <project>` with no path
- `DeployStackViewTest` — access control (anonymous→302, member→403, staff→303), and GET refused
- `StackDisparueTest` — reconciliation: a stack absent from a report loses `present`, a move leaves the old path behind, a `missing` compose stops alerting once gone, a redeploy comes back, a report without a `stacks` key changes nothing, and other machines are untouched
- `StacksPageDisparuesTest` — the alert stays while the stack is reported and goes out by itself when it is not, and a gone stack is counted nowhere else
- `ForgetStackViewTest` — the only delete in the console: access control, GET refused, a gone stack forgotten, a still-reported one refused, and the bulk sweep sparing what runs

`apps/core/tests.py` covers the console:
- `ConsoleAccessTest` — the three cases on a console page (anonymous→302, logged-in without group→403, viewer→200), plus viewer refused on a staff-only page
- `ConsoleMiddlewareScopeTest` — the regression that matters: a member without a console group keeps the public site and their own profile, and only `/console/` answers 403
- `ConsolePageMixinTest` — title, active nav entry and sub-navigation; object-dependent titles; and that no page falls back to a generic "Console" title
- `FleetStacksPageTest` — the stacks page: template, active sub-page, and machines without a stack excluded

Run them in Docker: `docker compose exec web python /app/multisite/manage.py test`. Tests need PostgreSQL, so bring `db` up first. Use a distinct `DB_NAME` if another test run may be in flight (the test database is `test_<DB_NAME>`).
