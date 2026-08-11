#!/usr/bin/env bash
#
# All-in-one deployment for argawaen.net: git, build, start, health check.
#
# Migrations and collectstatic are run by entrypoint.sh when the `web` container
# starts, so this script does not repeat them.
#
#   ./deploy.sh                 full deployment (pull + build + up + wait)
#   ./deploy.sh --no-pull       skip the git update
#   ./deploy.sh --tests         run the test suite before starting
#   ./deploy.sh --dry-run       print what would run, execute nothing
#   ./deploy.sh status          service status
#   ./deploy.sh logs [service]  follow the logs
#   ./deploy.sh stop            stop everything
#   ./deploy.sh restart         restart without rebuilding
#   ./deploy.sh tests [app]     run the tests
#   ./deploy.sh superuser       create an admin account
#   ./deploy.sh shell           Django shell inside the web container
#   ./deploy.sh help            this help
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MANAGE=(python /app/multisite/manage.py)
# Only these services carry a healthcheck, so only these can be waited on.
WATCHED_SERVICES=(db redis web)
HEALTH_TIMEOUT=180

PULL=1
TESTS=0
DRY_RUN=0

# --- Output ------------------------------------------------------------------

if [ -t 1 ]; then
    C_STEP=$'\033[1;34m'; C_OK=$'\033[0;32m'; C_WARN=$'\033[0;33m'
    C_ERR=$'\033[0;31m'; C_END=$'\033[0m'
else
    C_STEP=""; C_OK=""; C_WARN=""; C_ERR=""; C_END=""
fi

step() { printf '\n%s==> %s%s\n' "$C_STEP" "$1" "$C_END"; }
ok()   { printf '%s  ✓ %s%s\n' "$C_OK" "$1" "$C_END"; }
warn() { printf '%s  ! %s%s\n' "$C_WARN" "$1" "$C_END"; }
fail() { printf '%s  ✗ %s%s\n' "$C_ERR" "$1" "$C_END" >&2; exit 1; }

# Run a command, or just print it in --dry-run mode.
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] %s\n' "$*"
        return 0
    fi
    "$@"
}

# The help text is the file header: one place to keep up to date.
usage() {
    awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "${BASH_SOURCE[0]}"
}

# --- Preflight checks --------------------------------------------------------

check_tools() {
    command -v docker >/dev/null 2>&1 || fail "docker not found."
    docker compose version >/dev/null 2>&1 \
        || fail "the 'docker compose' plugin is missing (docker-compose v1 is not supported)."
    docker info >/dev/null 2>&1 \
        || fail "the docker daemon is not responding: is it running, and is your account in the docker group?"
    ok "docker and docker compose available"
}

check_env() {
    if [ ! -f .env ]; then
        warn ".env missing, copying .env.example"
        cp .env.example .env
        fail "edit .env (at least DJANGO_SECRET_KEY, DB_PASSWORD, POSTGRES_PASSWORD) then run again."
    fi
    # Leftover example values are the number one cause of a failed deployment.
    local leftovers
    leftovers="$(grep -c 'change-me' .env || true)"
    if [ "$leftovers" -gt 0 ]; then
        warn "$leftovers 'change-me' value(s) still in .env"
    fi
    ok ".env present"
}

# Read a variable from .env, falling back to the given default.
env_value() {
    local key="$1" default="${2:-}" line
    line="$(grep -E "^${key}=" .env 2>/dev/null | tail -1 || true)"
    if [ -z "$line" ]; then
        printf '%s' "$default"
    else
        printf '%s' "${line#*=}"
    fi
}

# The media directory must exist *before* the first `up`: otherwise Docker creates
# it as root and the owner can no longer clean it. The PostgreSQL directory is left
# to Docker on purpose, since initdb requires owning it.
prepare_directories() {
    local media
    media="$(env_value SERVER_PATH_MEDIA ./docker_data/media)"
    if [ ! -d "$media" ]; then
        run mkdir -p "$media"
        ok "media directory created: $media"
    fi
}

# The lab inventory is mounted read-only. Without it the Fleet page can only show
# machines that already reported, which is degraded but not fatal.
check_inventory() {
    local inventory
    inventory="$(env_value INVENTORY_FILE /srv/home-server-stacks/_common/inventory.conf)"
    if [ ! -f "$inventory" ]; then
        warn "inventory not found: $inventory (the Fleet page will be incomplete)"
    else
        ok "inventory found: $inventory"
    fi
}

# --- Steps -------------------------------------------------------------------

update_repository() {
    step "Updating the repository"
    if [ ! -d .git ]; then
        warn "not a git repository, skipping the update"
        return 0
    fi
    if [ -n "$(git status --porcelain)" ]; then
        git status --short
        fail "the repository has local changes: commit them, stash them, or use --no-pull."
    fi
    local before
    before="$(git rev-parse HEAD)"
    run git pull --ff-only
    if [ "$DRY_RUN" -eq 0 ]; then
        local after
        after="$(git rev-parse HEAD)"
        if [ "$before" = "$after" ]; then
            ok "already up to date ($(git rev-parse --short HEAD))"
        else
            ok "updated: $(git rev-parse --short "$before") -> $(git rev-parse --short "$after")"
            git --no-pager log --oneline "$before..$after"
        fi
    fi
}

build_image() {
    step "Building the image"
    run docker compose build
    ok "image built"
}

run_tests() {
    local target="${1:-}"
    step "Tests${target:+ ($target)}"
    # In a throwaway container with a dedicated test database: touches neither the
    # production database nor the running services.
    run docker compose run --rm --no-deps \
        -e DB_NAME="$(env_value DB_NAME argawaen)_deploytest" \
        --entrypoint python web /app/multisite/manage.py test ${target:+"$target"} --noinput
    ok "tests passed"
}

start_services() {
    step "Starting the services"
    run docker compose up -d
    ok "services started"
}

# Wait for a service to become healthy, or fail showing its last log lines.
wait_for_service() {
    local service="$1" elapsed=0 cid health status
    cid="$(docker compose ps -q "$service" 2>/dev/null || true)"
    [ -n "$cid" ] || fail "service $service did not start."

    while [ "$elapsed" -lt "$HEALTH_TIMEOUT" ]; do
        status="$(docker inspect -f '{{.State.Status}}' "$cid")"
        [ "$status" = "running" ] || break
        health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cid")"
        case "$health" in
            healthy|no-healthcheck) ok "$service: $health"; return 0 ;;
            unhealthy) break ;;
        esac
        sleep 3
        elapsed=$((elapsed + 3))
        printf '\r  ... %s: %s (%ss)' "$service" "$health" "$elapsed"
    done
    printf '\n'
    docker compose logs --tail 40 "$service" || true
    fail "$service did not become operational within ${HEALTH_TIMEOUT}s."
}

check_health() {
    step "Checking health"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] would wait for: %s\n' "${WATCHED_SERVICES[*]}"
        return 0
    fi
    local service
    for service in "${WATCHED_SERVICES[@]}"; do
        wait_for_service "$service"
    done
}

summary() {
    step "Service status"
    docker compose ps
    local port
    port="$(env_value SERVER_PORT 8000)"
    printf '\n'
    ok "site available at http://localhost:${port}/"
    printf '     console: http://localhost:%s/console/\n' "$port"
    printf '     logs:    ./deploy.sh logs\n'
}

deploy() {
    step "Deploying argawaen.net"
    [ "$DRY_RUN" -eq 1 ] && warn "--dry-run mode: no command is executed"
    check_tools
    check_env
    check_inventory
    prepare_directories
    [ "$PULL" -eq 1 ] && update_repository
    build_image
    [ "$TESTS" -eq 1 ] && run_tests
    start_services
    check_health
    [ "$DRY_RUN" -eq 0 ] && summary
    return 0
}

# --- Entry point -------------------------------------------------------------

COMMAND="deploy"
ARGUMENT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --no-pull)  PULL=0 ;;
        --tests)    TESTS=1 ;;
        --dry-run)  DRY_RUN=1 ;;
        -h|--help|help) usage; exit 0 ;;
        deploy|status|logs|stop|restart|tests|superuser|shell)
            COMMAND="$1"
            if [ $# -gt 1 ] && [[ "$2" != -* ]]; then
                ARGUMENT="$2"
                shift
            fi
            ;;
        *) fail "unknown argument: $1 (see ./deploy.sh help)" ;;
    esac
    shift
done

case "$COMMAND" in
    deploy)    deploy ;;
    status)    check_tools; docker compose ps ;;
    logs)      docker compose logs -f ${ARGUMENT:+"$ARGUMENT"} ;;
    stop)      step "Stopping"; docker compose down; ok "services stopped" ;;
    restart)   step "Restarting"; docker compose restart; check_health; summary ;;
    tests)     check_tools; check_env; run_tests "$ARGUMENT" ;;
    superuser) docker compose exec web "${MANAGE[@]}" createsuperuser ;;
    shell)     docker compose exec web "${MANAGE[@]}" shell ;;
esac
