#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="九联光猫获取超级密码工具"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BUILD="$(tr -d '[:space:]' < "$ROOT/BUILD_NUMBER")"
DIST="$ROOT/dist"
APP="$DIST/$APP_NAME.app"
DMG="$DIST/$APP_NAME-$VERSION-build$BUILD.dmg"
STAGE="$DIST/dmg-stage"

if [[ ! -d "$APP" ]]; then
  echo "App not found: $APP" >&2
  exit 1
fi

rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME $VERSION build$BUILD" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
hdiutil verify "$DMG"
rm -rf "$STAGE"

echo "$DMG"
