#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="九联光猫获取超级密码工具"
EXEC_NAME="JiulianSuperPasswordTool"
BUNDLE_ID="local.jiulian.superpassword"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BUILD="$(tr -d '[:space:]' < "$ROOT/BUILD_NUMBER")"
DERIVED="$ROOT/derived"
DIST="$ROOT/dist"
APP="$DIST/$APP_NAME.app"

rm -rf "$DERIVED" "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources" "$DIST"

"$ROOT/scripts/generate_version.sh"
swift build -c release --package-path "$ROOT" --scratch-path "$DERIVED/.build"
cp "$DERIVED/.build/release/$EXEC_NAME" "$APP/Contents/MacOS/$EXEC_NAME"
chmod 755 "$APP/Contents/MacOS/$EXEC_NAME"
cp "$ROOT/shared/backend/jiulian_backend_helper.py" "$APP/Contents/Resources/jiulian_backend_helper.py"
chmod 755 "$APP/Contents/Resources/jiulian_backend_helper.py"
cp "$ROOT/platforms/macos/Resources/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
chmod 644 "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
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
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

plutil -lint "$APP/Contents/Info.plist"
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
/usr/bin/ditto -c -k --keepParent "$APP" "$DIST/$APP_NAME-$VERSION.app.zip"

echo "$APP"
