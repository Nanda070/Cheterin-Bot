#!/usr/bin/env bash
# Thin alias so one command works from repo root: ./update.sh
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/update.sh" "$@"
