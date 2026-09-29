#!/usr/bin/env bash
# Full VPS update for Cheterin: git pull, Python deps, dashboard + Lookup SPA builds,
# then systemctl restart for bot/dashboard and Lookup API.
# Canonical (any cwd):
#   bash ~/Cheterin_Bot_Dashboard/update.sh
#
# Do not use sudo for git/pip/npm — run as the deploying user that owns the repo/venvs.
# systemctl restart may prompt for sudo unless NOPASSWD is configured (see deploy/systemd/README.md).
# This script does NOT SSH anywhere; it only mutates the local machine when you run it.
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")/.." && pwd)"
cd "$REPO_ROOT"

CHE_BOT_UNIT="${CHE_BOT_UNIT:-cheterin-bot.service}"
CHE_LOOKUP_UNIT="${CHE_LOOKUP_UNIT:-cheterin-lookup.service}"

echo "==> repo: $REPO_ROOT"

if [[ ! -d .git ]]; then
  echo "ERROR: $REPO_ROOT is not a git repo." >&2
  exit 1
fi

echo "==> git pull"
git pull

BOT_PYTHON="$REPO_ROOT/venv/bin/python"
if [[ ! -x "$BOT_PYTHON" ]]; then
  echo "ERROR: bot venv python not found at $BOT_PYTHON" >&2
  echo "Create it once:" >&2
  echo "  python3 -m venv venv" >&2
  echo "  ./venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

echo "==> pip install -r requirements.txt (bot + dashboard)"
"$BOT_PYTHON" -m pip install -r requirements.txt

LOOKUP_PYTHON="$REPO_ROOT/lookup-api/.venv/bin/python"
if [[ ! -x "$LOOKUP_PYTHON" ]]; then
  echo "==> lookup-api/.venv missing — using bot venv for Lookup API deps"
  LOOKUP_PYTHON="$BOT_PYTHON"
fi
echo "==> pip install -r lookup-api/requirements.txt"
"$LOOKUP_PYTHON" -m pip install -r "$REPO_ROOT/lookup-api/requirements.txt"

build_frontend() {
  local dir="$1"
  local label="$2"
  if [[ ! -d "$dir" ]]; then
    echo "ERROR: $dir not found ($label)." >&2
    exit 1
  fi
  echo "==> building $label ($dir)"
  cd "$dir"
  # Safe cache junk only — do not wipe node_modules or package-lock.json.
  rm -rf node_modules/.cache node_modules/.vite dist
  find . -depth -type d -name '_logs' -exec rm -rf {} \; 2>/dev/null || true
  if [[ -f package-lock.json ]]; then
    echo "==> npm ci ($label)"
    npm ci
  else
    echo "==> npm install ($label)"
    npm install
  fi
  echo "==> npm run build ($label)"
  npm run build
  cd "$REPO_ROOT"
}

build_frontend "$REPO_ROOT/dashboard/frontend" "dashboard frontend"
build_frontend "$REPO_ROOT/lookup" "Lookup SPA"

systemctl_restart() {
  local unit="$1"
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "WARN: systemctl not found — skip restart of $unit" >&2
    return 0
  fi
  echo "==> systemctl restart $unit"
  if [[ "$(id -u)" -eq 0 ]]; then
    systemctl restart "$unit"
  elif sudo -n systemctl restart "$unit" 2>/dev/null; then
    :
  else
    sudo systemctl restart "$unit"
  fi
}

systemctl_restart "$CHE_BOT_UNIT"
systemctl_restart "$CHE_LOOKUP_UNIT"

if command -v systemctl >/dev/null 2>&1; then
  echo "==> status"
  if [[ "$(id -u)" -eq 0 ]]; then
    systemctl --no-pager --full status "$CHE_BOT_UNIT" "$CHE_LOOKUP_UNIT" || true
  else
    sudo systemctl --no-pager --full status "$CHE_BOT_UNIT" "$CHE_LOOKUP_UNIT" || true
  fi
fi

echo "==> update complete (systemd: $CHE_BOT_UNIT + $CHE_LOOKUP_UNIT)"
echo "    Units live in deploy/systemd/ — install once per host; see deploy/systemd/README.md"
