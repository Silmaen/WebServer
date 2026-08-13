#!/usr/bin/env bash
#
# All-in-one deployment for argawaen.net: git, build, start, health check.
#
# Migrations and collectstatic are run by entrypoint.sh when the `web` container
# starts, so this script does not repeat them.
#
#   ./deploy.sh                 full deployment (pull + build + up + wait)
#   ./deploy.sh --no-pull       fetch nothing: neither the git update nor the images
#   ./deploy.sh --tests         run the test suite before starting
#   ./deploy.sh --dry-run       print what would run, execute nothing
#   ./deploy.sh check           only look for a pending update, change nothing
#   ./deploy.sh status          service status
#   ./deploy.sh logs [service]  follow the logs
#   ./deploy.sh stop            stop everything
#   ./deploy.sh restart         restart without rebuilding
#   ./deploy.sh tests [app]     run the tests
#   ./deploy.sh superuser       create an admin account
#   ./deploy.sh shell           Django shell inside the web container
#   ./deploy.sh help            this help
#
# `check` (alias `--check`) exits with a status meant to be scripted:
#   0   already up to date
#   10  an update is pending
#   1   cannot tell (not a git repository, no upstream, fetch failed)
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
#
# The trailing CR is stripped: a .env saved from Windows turns every value into
# `value<CR>`, and the consequences are silent rather than loud -- a path read that way
# points at a directory nothing else will ever produce, so this script creates a second
# media directory and reports the first one as missing.
env_value() {
    local key="$1" default="${2:-}" line
    line="$(grep -E "^${key}=" .env 2>/dev/null | tail -1 || true)"
    if [ -z "$line" ]; then
        printf '%s' "$default"
    else
        line="${line#*=}"
        printf '%s' "${line%$'\r'}"
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

# Report whether the remote is ahead, and touch nothing else. `git fetch` only writes
# remote-tracking refs, never the working tree, so this is safe to run on a schedule.
check_update() {
    step "Checking for a pending update"
    [ -d .git ] || fail "not a git repository, cannot check for updates."

    local branch upstream
    branch="$(git rev-parse --abbrev-ref HEAD)"
    [ "$branch" != "HEAD" ] || fail "detached HEAD: there is no branch to compare."
    # for-each-ref rather than `rev-parse --symbolic-full-name '@{upstream}'`: on a branch
    # with no upstream the latter echoes the literal `@{upstream}` back and exits 0, so the
    # guard below passed, the comparison below died on "ambiguous argument", and `check`
    # ended on exit 128 with three "integer expected" errors instead of the documented 1.
    # An empty string is an answer that can be tested.
    upstream="$(git for-each-ref --format='%(upstream:short)' "refs/heads/$branch")"
    [ -n "$upstream" ] || fail "branch '$branch' tracks no upstream: nothing to compare against."

    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] git fetch --quiet\n'
        warn "comparing against the remote refs already on disk"
    else
        git fetch --quiet || fail "git fetch failed: is the remote reachable?"
    fi

    local counts behind ahead
    counts="$(git rev-list --left-right --count "${upstream}...HEAD" 2>/dev/null)" \
        || fail "'$upstream' is not on disk: this branch was never pushed, or never fetched."
    read -r behind ahead <<< "$counts"
    ok "branch '$branch' tracking '$upstream'"

    # A dirty tree does not block this check, but it will block the deployment.
    if [ -n "$(git status --porcelain)" ]; then
        warn "local changes present: a deployment will need --no-pull"
    fi

    if [ "$ahead" -gt 0 ] && [ "$behind" -eq 0 ]; then
        ok "up to date ($ahead local commit(s) not pushed)"
        return 0
    fi

    if [ "$behind" -eq 0 ]; then
        ok "up to date ($(git rev-parse --short HEAD))"
        return 0
    fi

    if [ "$ahead" -gt 0 ]; then
        warn "branches have diverged: $behind incoming, $ahead local commit(s)"
    else
        warn "$behind commit(s) pending"
    fi
    git --no-pager log --oneline "HEAD..${upstream}"
    printf '\n     deploy with: ./deploy.sh\n'
    exit 10
}

# Refresh the images that come from a registry. Without this, a pinned tag like
# postgres:16-alpine stays on whatever was pulled the first time, so the minor
# releases -- which is where the security fixes are -- never land on the server.
# The Dockerfile's base image needs its own pull: `docker compose pull` skips the
# buildable services, and a year-old FROM is just as stale as a year-old postgres.
# The tags are read from the Dockerfile rather than repeated here -- every `FROM` of it,
# not just the first: `exit` after the first one was correct only as long as the build
# stayed single-stage, and the day a stage is added in front the real base image silently
# stops being refreshed. Stage names (`FROM x AS name`, then `FROM name`) are skipped,
# since they are not pullable references.
#
# A registry we cannot reach is a warning, not a failure: the images already on
# disk are enough to deploy, and aborting would leave the update half done.
pull_images() {
    step "Refreshing the images"
    local stale=0 stages base
    run docker compose pull --ignore-buildable --quiet || stale=1
    stages="$(awk 'toupper($1) == "FROM" && toupper($3) == "AS" { print $4 }' Dockerfile 2>/dev/null || true)"
    while read -r base; do
        [ -n "$base" ] || continue
        [ "$base" = "scratch" ] && continue
        printf '%s\n' "$stages" | grep -qxF "$base" && continue
        run docker pull --quiet "$base" || stale=1
    done < <(awk 'toupper($1) == "FROM" { print $2 }' Dockerfile 2>/dev/null | sort -u)
    if [ "$stale" -eq 1 ]; then
        warn "some images could not be refreshed, keeping the ones already on disk"
    else
        ok "images up to date"
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
    # Asked of the running container rather than of .env: an operator who exports
    # SERVER_PORT for one run must not be told the port the file says.
    port="$(docker compose port web 8000 2>/dev/null | head -1 | sed 's/.*://')"
    [ -n "$port" ] || port="$(env_value SERVER_PORT 8000)"
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
    [ "$PULL" -eq 1 ] && pull_images
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
        --check)    COMMAND="check" ;;
        deploy|check|status|logs|stop|restart|tests|superuser|shell)
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
    check)     check_update ;;
    status)    check_tools; docker compose ps ;;
    logs)      docker compose logs -f ${ARGUMENT:+"$ARGUMENT"} ;;
    stop)      step "Stopping"; docker compose down; ok "services stopped" ;;
    restart)   step "Restarting"; docker compose restart; check_health; summary ;;
    tests)     check_tools; check_env; run_tests "$ARGUMENT" ;;
    superuser) docker compose exec web "${MANAGE[@]}" createsuperuser ;;
    shell)     docker compose exec web "${MANAGE[@]}" shell ;;
esac
