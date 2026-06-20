#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="九联光猫获取超级密码工具"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BUILD="$(tr -d '[:space:]' < "$ROOT/BUILD_NUMBER")"
NAS_ROOT="${JIULIAN_RELEASE_ARCHIVE_ROOT:-/Volumes/西数紫盘4T/jiulian-super-password-tool-releases}"
DIST="$ROOT/dist"
DMG="$DIST/$APP_NAME-$VERSION-build$BUILD.dmg"
ZIP="$DIST/$APP_NAME-$VERSION.app.zip"

# The archive target is optional: local builds must still succeed when the NAS
# disk is not mounted.
NAS_PARENT="$(dirname "$NAS_ROOT")"
if [[ ! -d "$NAS_PARENT" ]]; then
  echo "Release archive skipped: NAS parent not found: $NAS_PARENT"
  exit 0
fi

if [[ ! -f "$DMG" || ! -f "$ZIP" ]]; then
  echo "Release archive skipped: expected local artifacts not found." >&2
  echo "  $DMG" >&2
  echo "  $ZIP" >&2
  exit 0
fi

DEST="$NAS_ROOT/v$VERSION/build$BUILD"
mkdir -p "$DEST"
cp -f "$DMG" "$DEST/"
cp -f "$ZIP" "$DEST/"

{
  echo "Project: jiulian-super-password-tool"
  echo "Version: $VERSION"
  echo "Build: $BUILD"
  echo "Git commit: $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "Git branch: $(git -C "$ROOT" branch --show-current 2>/dev/null || echo unknown)"
  echo "Archived at: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "Source dist: $DIST"
  echo "Archive dir: $DEST"
  echo "Artifacts:"
  basename "$DMG"
  basename "$ZIP"
} > "$DEST/BUILD_INFO.txt"

echo "Release artifacts archived to: $DEST"
