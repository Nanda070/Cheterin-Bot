#!/usr/bin/env bash
# VPS update: git pull, deps, dashboard + Lookup builds, systemctl restart.
# Canonical (any cwd):
#   bash ~/Cheterin_Bot_Dashboard/update.sh
# Do not use sudo for the whole script — git/pip/npm must run as the deploying user.
# systemctl restart inside scripts/update.sh may use sudo for the two Cheterin units only.
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")" && pwd)"

exec "$REPO_ROOT/scripts/update.sh" "$@"
