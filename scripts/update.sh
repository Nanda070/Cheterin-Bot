#!/usr/bin/env bash
# One-command VPS update for Cheterin: git pull, venv deps, frontend build, tmux attach.
# Canonical (any cwd, no sudo):
#   bash ~/Cheterin_Bot_Dashboard/update.sh
# Do not use sudo — git/pip/npm/tmux must run as the deploying user;
# sudo would break venv activation and tmux attach.
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")/.." && pwd)"
cd "$REPO_ROOT"

TMUX_SESSION="${TMUX_SESSION:-chetmain}"

echo "==> repo: $REPO_ROOT"

if [[ ! -d .git ]]; then
  echo "ERROR: $REPO_ROOT is not a git repo." >&2
  exit 1
fi

echo "==> git pull"
git pull

VENV_ACTIVATE="$REPO_ROOT/venv/bin/activate"
if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "ERROR: venv not found at $VENV_ACTIVATE" >&2
  echo "Create it once:" >&2
  echo "  python3 -m venv venv" >&2
  echo "  source venv/bin/activate" >&2
  echo "  pip install -r requirements.txt" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_ACTIVATE"
echo "==> pip install -r requirements.txt"
python -m pip install -r requirements.txt

FRONTEND="$REPO_ROOT/dashboard/frontend"
if [[ ! -d "$FRONTEND" ]]; then
  echo "ERROR: dashboard/frontend not found." >&2
  exit 1
fi

cd "$FRONTEND"

echo "==> cleaning node build caches"
# Safe cache junk only — do not wipe node_modules or package-lock.json.
rm -rf node_modules/.cache node_modules/.vite dist
find . -depth -type d -name '_logs' -exec rm -rf {} \; 2>/dev/null || true

if [[ -f package-lock.json ]]; then
  echo "==> npm ci"
  npm ci
else
  echo "==> npm install"
  npm install
fi
echo "==> npm run build"
npm run build
cd "$REPO_ROOT"

echo "==> tmux attach -t $TMUX_SESSION"
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  exec tmux attach -t "$TMUX_SESSION"
fi

echo "No tmux session named '$TMUX_SESSION'." >&2
echo "Start one:  tmux new -s $TMUX_SESSION" >&2
echo "Or list:    tmux ls" >&2
exit 1
