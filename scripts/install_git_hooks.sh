#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install -m 755 "$ROOT/hooks/pre-commit" "$ROOT/.git/hooks/pre-commit"
echo "Installed git pre-commit hook: $ROOT/.git/hooks/pre-commit"
