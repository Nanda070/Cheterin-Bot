#!/usr/bin/env bash
# VPS update: git pull, venv deps, frontend build, tmux attach.
# Canonical (any cwd, no sudo):
#   bash ~/Cheterin_Bot_Dashboard/update.sh
# Do not use sudo — git/pip/npm/tmux must run as the deploying user;
# sudo would break venv activation and tmux attach (unlike Cheterin-Media's
# sudo bash ~/Cheterin-Media/deploy/oracle/build-web.sh).
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")" && pwd)"

exec "$REPO_ROOT/scripts/update.sh" "$@"
