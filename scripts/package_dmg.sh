#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="九联光猫获取超级密码工具"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BUILD="$(tr -d '[:space:]' < "$ROOT/BUILD_NUMBER")"
DIST="$ROOT/dist"
DIST_APP="$DIST/$APP_NAME.app"
DMG="$DIST/$APP_NAME-$VERSION-build$BUILD.dmg"

LOCAL_BUILD_ROOT="${TMPDIR:-/tmp}/jiulian-super-password-tool-build"
LOCAL_APP="$LOCAL_BUILD_ROOT/$APP_NAME.app"
LOCAL_STAGE="$LOCAL_BUILD_ROOT/dmg-stage"
LOCAL_DMG="$LOCAL_BUILD_ROOT/$APP_NAME-$VERSION-build$BUILD.dmg"

# Prefer the locally signed bundle created by build_app.sh. Network volumes can
# add metadata that breaks codesign validation or pollutes the DMG.
if [[ -d "$LOCAL_APP" ]]; then
  APP="$LOCAL_APP"
elif [[ -d "$DIST_APP" ]]; then
  APP="$DIST_APP"
else
  echo "App not found: $DIST_APP" >&2
  exit 1
fi

rm -rf "$LOCAL_STAGE" "$LOCAL_DMG" "$DMG"
mkdir -p "$LOCAL_STAGE" "$DIST"
/usr/bin/ditto "$APP" "$LOCAL_STAGE/$APP_NAME.app"
ln -s /Applications "$LOCAL_STAGE/Applications"
if command -v xattr >/dev/null 2>&1; then
  xattr -cr "$LOCAL_STAGE" || true
fi
hdiutil create -volname "$APP_NAME $VERSION build$BUILD" -srcfolder "$LOCAL_STAGE" -ov -format UDZO "$LOCAL_DMG"
hdiutil verify "$LOCAL_DMG"
cp "$LOCAL_DMG" "$DMG"
rm -rf "$LOCAL_STAGE"

echo "$DMG"
