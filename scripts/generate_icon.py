#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets" / "AppIcon"
SOURCE = ASSETS / "source"
MACOS = ASSETS / "macos"
WINDOWS = ASSETS / "windows"
ICONSET = MACOS / "AppIcon.iconset"
PNG1024 = SOURCE / "AppIcon-1024.png"
ICNS = MACOS / "AppIcon.icns"
ICO = WINDOWS / "AppIcon.ico"

SOURCE.mkdir(parents=True, exist_ok=True)
MACOS.mkdir(parents=True, exist_ok=True)
WINDOWS.mkdir(parents=True, exist_ok=True)
ICONSET.mkdir(parents=True, exist_ok=True)

S = 1024
cx = cy = S // 2

# macOS app icons are visually rounded-square/squircle, not a hard white square.
# Build at high resolution then downsample so the rounded white edge is clean.
SS = 4
L = S * SS
img = Image.new("RGBA", (L, L), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# White rounded icon plate fills the whole macOS-style icon shape.
# The outside corner pixels are transparent because they are outside the rounded icon.
corner_radius = 230 * SS
d.rounded_rectangle((0, 0, L - 1, L - 1), radius=corner_radius, fill=(255, 255, 255, 255))

# Large centered blue circle inside the white rounded icon plate.
R = 405 * SS
for y in range(cy * SS - R, cy * SS + R + 1):
    for x in range(cx * SS - R, cx * SS + R + 1):
        dx, dy = x - cx * SS, y - cy * SS
        if dx * dx + dy * dy <= R * R:
            t = (dy + R) / (2 * R)
            rr = int(37 - 10 * t)
            gg = int(184 - 28 * t)
            bb = int(236 - 2 * t)
            img.putpixel((x, y), (rr, gg, bb, 255))

d = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
blue_cut = (32, 168, 231, 255)

def sc(v):
    return int(round(v * SS))

# White network-device glyph.
arc_center_y = sc(405)
for r, width in [(82, 15), (150, 14)]:
    rr = sc(r)
    bbox = (sc(cx) - rr, arc_center_y - rr, sc(cx) + rr, arc_center_y + rr)
    d.arc(bbox, start=210, end=330, fill=white, width=sc(width))
d.ellipse((sc(cx - 16), sc(405 - 16), sc(cx + 16), sc(405 + 16)), fill=white)

# Antennas kept inside the blue circle.
d.line((sc(382), sc(535), sc(318), sc(415)), fill=white, width=sc(20))
d.line((sc(642), sc(535), sc(706), sc(415)), fill=white, width=sc(20))
d.ellipse((sc(308), sc(405), sc(328), sc(425)), fill=white)
d.ellipse((sc(696), sc(405), sc(716), sc(425)), fill=white)

# Modem body.
d.rounded_rectangle((sc(318), sc(528), sc(706), sc(660)), radius=sc(38), fill=white)
d.rounded_rectangle((sc(365), sc(612), sc(659), sc(642)), radius=sc(14), fill=blue_cut)
d.ellipse((sc(372), sc(558), sc(430), sc(616)), fill=blue_cut)
d.ellipse((sc(392), sc(578), sc(410), sc(596)), fill=white)
for x in (532, 592):
    d.ellipse((sc(x - 12), sc(585 - 12), sc(x + 12), sc(585 + 12)), fill=blue_cut)
    d.ellipse((sc(x - 5), sc(585 - 5), sc(x + 5), sc(585 + 5)), fill=white)

img = img.resize((S, S), Image.Resampling.LANCZOS)
img.save(PNG1024)

sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]
for size, name in sizes:
    img.resize((size, size), Image.Resampling.LANCZOS).save(ICONSET / name)

import subprocess
subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)], check=True)
# Windows .ico：从 1024 原图直接生成，PIL 内部每帧独立 LANCZOS 缩放
ico_sizes = [(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(128,128),(256,256)]
img.save(ICO, format="ICO", sizes=ico_sizes)
print(PNG1024)
print(ICONSET)
print(ICNS)
print(ICO)
