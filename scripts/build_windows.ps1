param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

$version = (Get-Content VERSION -Raw).Trim()
$build = (Get-Content BUILD_NUMBER -Raw).Trim()
$dist = Join-Path $ProjectRoot "dist\windows"
$work = Join-Path $ProjectRoot "derived\pyinstaller-windows"
$icon = Join-Path $ProjectRoot "Assets\AppIcon\windows\AppIcon.ico"
New-Item -ItemType Directory -Force -Path $dist | Out-Null
New-Item -ItemType Directory -Force -Path $work | Out-Null

python -m pip install --upgrade pip
python -m pip install pyinstaller

if (!(Test-Path $icon)) { throw "Windows icon asset not found: $icon" }

$name = "JiulianSuperPasswordTool-$version-build$build-win-x64"
$sep = [IO.Path]::PathSeparator
$entry = Join-Path $ProjectRoot "platforms\windows\jiulian_windows_tool.py"
$backendData = "$(Join-Path $ProjectRoot 'shared\backend\jiulian_backend_helper.py')${sep}shared/backend"
$backendVendorData = "$(Join-Path $ProjectRoot 'shared\backend\vendor')${sep}shared/backend/vendor"
$versionData = "$(Join-Path $ProjectRoot 'VERSION')${sep}."
$buildData = "$(Join-Path $ProjectRoot 'BUILD_NUMBER')${sep}."

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name $name `
  --icon $icon `
  --distpath $dist `
  --workpath $work `
  --specpath $work `
  --add-data $backendData `
  --add-data $backendVendorData `
  --add-data $versionData `
  --add-data $buildData `
  $entry

$exe = Join-Path $dist "$name.exe"
if (!(Test-Path $exe)) { throw "Build failed: $exe not found" }
Get-Item $exe | Format-List FullName,Length,LastWriteTime
