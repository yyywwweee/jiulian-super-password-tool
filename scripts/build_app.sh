#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="九联光猫获取超级密码工具"
EXEC_NAME="JiulianSuperPasswordTool"
BUNDLE_ID="com.jiulian.superpassword-tool"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BUILD="$(tr -d '[:space:]' < "$ROOT/BUILD_NUMBER")"
GIT_COMMIT="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILD_TIME="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
DIST="$ROOT/dist"

# Build intermediates and code signing on SMB/network/external volumes can fail
# or leave undeletable temporary trees. Keep transient build state local.
# "resource fork, Finder information, or similar detritus not allowed".
# Build/sign/package the .app on the local filesystem, then copy artifacts back.
LOCAL_BUILD_ROOT="${TMPDIR:-/tmp}/jiulian-super-password-tool-build"
DERIVED="$LOCAL_BUILD_ROOT/derived"
LOCAL_APP="$LOCAL_BUILD_ROOT/$APP_NAME.app"
LOCAL_ZIP="$LOCAL_BUILD_ROOT/$APP_NAME-$VERSION.app.zip"
APP="$DIST/$APP_NAME.app"
ZIP="$DIST/$APP_NAME-$VERSION.app.zip"

rm -rf "$LOCAL_BUILD_ROOT" "$APP" "$ZIP"
mkdir -p "$LOCAL_APP/Contents/MacOS" "$LOCAL_APP/Contents/Resources" "$DIST"

swift build -c release --package-path "$ROOT" --scratch-path "$DERIVED/.build"
cp "$DERIVED/.build/release/$EXEC_NAME" "$LOCAL_APP/Contents/MacOS/$EXEC_NAME"
chmod 755 "$LOCAL_APP/Contents/MacOS/$EXEC_NAME"
cp "$ROOT/shared/backend/jiulian_backend_helper.py" "$LOCAL_APP/Contents/Resources/jiulian_backend_helper.py"
chmod 755 "$LOCAL_APP/Contents/Resources/jiulian_backend_helper.py"
mkdir -p "$LOCAL_APP/Contents/Resources/vendor"
cp "$ROOT/shared/backend/vendor/telnetlib_compat.py" "$LOCAL_APP/Contents/Resources/vendor/telnetlib_compat.py"
chmod 644 "$LOCAL_APP/Contents/Resources/vendor/telnetlib_compat.py"
cp "$ROOT/Assets/AppIcon/macos/AppIcon.icns" "$LOCAL_APP/Contents/Resources/AppIcon.icns"
chmod 644 "$LOCAL_APP/Contents/Resources/AppIcon.icns"

cat > "$LOCAL_APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_CN</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleExecutable</key>
    <string>$EXEC_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$BUILD</string>
    <key>JiulianGitCommit</key>
    <string>$GIT_COMMIT</string>
    <key>JiulianBuildTime</key>
    <string>$BUILD_TIME</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

plutil -lint "$LOCAL_APP/Contents/Info.plist"
if command -v xattr >/dev/null 2>&1; then
  xattr -cr "$LOCAL_APP" || true
fi
codesign --force --deep --sign - "$LOCAL_APP"
codesign --verify --deep --strict --verbose=2 "$LOCAL_APP"
/usr/bin/ditto -c -k --keepParent "$LOCAL_APP" "$LOCAL_ZIP"

# Preserve the signed app as an artifact in dist. ditto is safer than cp for bundles.
/usr/bin/ditto "$LOCAL_APP" "$APP"
cp "$LOCAL_ZIP" "$ZIP"

# The copied app on network storage may not be suitable for re-signing there,
# but the ZIP/DMG are produced from the signed local bundle.
echo "$APP"
