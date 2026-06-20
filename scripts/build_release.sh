#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/build_app.sh"
"$ROOT/scripts/package_dmg.sh"
"$ROOT/scripts/archive_release_to_nas.sh"
