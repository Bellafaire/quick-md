#!/usr/bin/env bash
#
# run.sh - launch quick-md in a Docker container via `docker run`.
#
# This script replaces the docker-compose workflow. It allows you to configure
# everything that was previously configured in docker-compose.yml through
# command-line flags and environment variables, and it supports running
# multiple independent instances side by side (different notebooks / ports /
# container names).
#
# Usage:
#   ./run.sh [options]
#
# Options:
#   -n, --notebook PATH       Path to your notebook directory (mounted into the
#                             container). Defaults to the parent of this repo
#                             (i.e. the directory that contains quick-md/).
#   -p, --port PORT           Host port to expose the web server on. Default 6580.
#   -c, --container NAME      Container name. Default "quick_md_notebook".
#                             Override this when running multiple instances.
#   --password PASSWORD       Enable password protection with the given password.
#                             If omitted but --password-protect is set, the
#                             $QUICK_MD_PASSWORD env var is used (or prompted).
#   --password-protect        Enable password protection. Reads the password from
#                             --password, the QUICK_MD_PASSWORD env var, or a
#                             prompt.
#   --screenshots PATH        Optional read-only mount of a host screenshots dir.
#   --videos PATH             Optional read-only mount of a host videos dir.
#   --build                   Force a rebuild of the image before starting.
#   -d, --detach              Run in the background (detached).
#   --image NAME              Image name to build/use. Default "quick-md".
#   -h, --help                Show this help message.
#
# Environment variables (used as defaults, flags take precedence):
#   QUICK_MD_NOTEBOOK         Notebook path
#   QUICK_MD_PORT             Host port
#   QUICK_MD_CONTAINER        Container name
#   QUICK_MD_IMAGE            Image name
#   QUICK_MD_PASSWORD         Password (when --password-protect is set)
#   USER_ID / GROUP_ID        UID/GID to build/run as (default: id -u / id -g)

set -euo pipefail

# ---- Defaults ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

NOTEBOOK="${QUICK_MD_NOTEBOOK:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PORT="${QUICK_MD_PORT:-6580}"
CONTAINER="${QUICK_MD_CONTAINER:-quick_md_notebook}"
IMAGE="${QUICK_MD_IMAGE:-quick-md}"
USER_ID="${USER_ID:-$(id -u)}"
GROUP_ID="${GROUP_ID:-$(id -g)}"
PASSWORD=""
PASSWORD_PROTECT=0
SCREENSHOTS=""
VIDEOS=""
FORCE_BUILD=0
DETACH=0

usage() {
    grep '^#' "$0" | sed '1d; s/^# \{0,1\}//'
    exit 0
}

# ---- Parse args ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--notebook)      NOTEBOOK="$2"; shift 2 ;;
        -p|--port)          PORT="$2"; shift 2 ;;
        -c|--container)     CONTAINER="$2"; shift 2 ;;
        --image)            IMAGE="$2"; shift 2 ;;
        --password)         PASSWORD="$2"; shift 2 ;;
        --password-protect) PASSWORD_PROTECT=1; shift ;;
        --screenshots)      SCREENSHOTS="$2"; shift 2 ;;
        --videos)           VIDEOS="$2"; shift 2 ;;
        --build)            FORCE_BUILD=1; shift ;;
        -d|--detach)        DETACH=1; shift ;;
        -h|--help)          usage ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# Resolve absolute notebook path
NOTEBOOK="$(cd "$NOTEBOOK" 2>/dev/null && pwd || echo "$NOTEBOOK")"

# ---- Resolve password ----
PASSWORD_FLAG=""
if [[ $PASSWORD_PROTECT -eq 1 ]]; then
    if [[ -z "$PASSWORD" ]]; then
        PASSWORD="${QUICK_MD_PASSWORD:-}"
    fi
    if [[ -z "$PASSWORD" ]]; then
        read -s -p "Enter password for web server: " PASSWORD
        echo ""
        if [[ -z "$PASSWORD" ]]; then
            echo "Error: password cannot be empty" >&2
            exit 1
        fi
    fi
    PASSWORD_FLAG="--password-protect"
fi

# ---- Build the image if missing or forced ----
NEED_BUILD=0
if [[ $FORCE_BUILD -eq 1 ]]; then
    NEED_BUILD=1
elif ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    NEED_BUILD=1
fi

if [[ $NEED_BUILD -eq 1 ]]; then
    echo "Building Docker image '$IMAGE'..."
    docker build \
        --build-arg USER_ID="$USER_ID" \
        --build-arg GROUP_ID="$GROUP_ID" \
        -t "$IMAGE" \
        "$SCRIPT_DIR"
fi

# ---- Stop & remove any existing container with the same name ----
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "Stopping existing container '$CONTAINER'..."
    docker rm -f "$CONTAINER" >/dev/null
fi

# ---- Assemble the docker run command ----
RUN_ARGS=(
    --name "$CONTAINER"
    -p "${PORT}:6580"
    -v "${NOTEBOOK}:/notebook"
    -e "PORT=${PORT}"
    --restart unless-stopped
)

if [[ -n "$PASSWORD_FLAG" ]]; then
    RUN_ARGS+=( -e "QUICK_MD_PASSWORD=${PASSWORD}" )
fi

if [[ -n "$SCREENSHOTS" ]]; then
    RUN_ARGS+=( -v "${SCREENSHOTS}:/screenshots:ro" )
fi
if [[ -n "$VIDEOS" ]]; then
    RUN_ARGS+=( -v "${VIDEOS}:/videos:ro" )
fi

if [[ $DETACH -eq 1 ]]; then
    RUN_ARGS+=( -d )
else
    RUN_ARGS+=( -it )
fi

# Application command inside the container
RUN_ARGS+=( "$IMAGE" python3 main.py --web-only --port 6580 $PASSWORD_FLAG )

echo "Starting container '$CONTAINER' on host port ${PORT} (notebook: ${NOTEBOOK})..."
docker run "${RUN_ARGS[@]}"