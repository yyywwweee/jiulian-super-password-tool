param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

$version = (Get-Content VERSION -Raw).Trim()
$build = (Get-Content BUILD_NUMBER -Raw).Trim()
$dist = Join-Path $ProjectRoot "dist\windows"
$work = Join-Path $ProjectRoot "derived\pyinstaller-windows"
$icon = Join-Path $ProjectRoot "Assets\AppIcon.ico"
New-Item -ItemType Directory -Force -Path $dist | Out-Null
New-Item -ItemType Directory -Force -Path $work | Out-Null

python -m pip install --upgrade pip
python -m pip install pyinstaller pillow

$iconScript = @'
from PIL import Image
from pathlib import Path
root = Path.cwd()
src = root / "Assets" / "AppIcon-1024.png"
out = root / "Assets" / "AppIcon.ico"
im = Image.open(src).convert("RGBA")
im.save(out, sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(out)
'@
$iconScriptPath = Join-Path $work "generate_ico.py"
Set-Content -Path $iconScriptPath -Value $iconScript -Encoding UTF8
python $iconScriptPath

$name = "JiulianSuperPasswordTool-$version-build$build-win-x64"
$sep = [IO.Path]::PathSeparator
$entry = Join-Path $ProjectRoot "platforms\windows\jiulian_windows_tool.py"
$backendData = "$(Join-Path $ProjectRoot 'Resources\jiulian_backend_helper.py')${sep}Resources"
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
  --add-data $versionData `
  --add-data $buildData `
  $entry

$exe = Join-Path $dist "$name.exe"
if (!(Test-Path $exe)) { throw "Build failed: $exe not found" }
Get-Item $exe | Format-List FullName,Length,LastWriteTime
