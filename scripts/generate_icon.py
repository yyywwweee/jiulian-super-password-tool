#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets"
ICONSET = ASSETS / "AppIcon.iconset"
PNG1024 = ASSETS / "AppIcon-1024.png"

ASSETS.mkdir(parents=True, exist_ok=True)
ICONSET.mkdir(parents=True, exist_ok=True)

S = 1024
img = Image.new("RGBA", (S, S), (250, 251, 250, 255))

# Full white/light-gray background across the whole icon canvas.
# No transparent outer margin, matching the user's request: whole icon background is white.
d = ImageDraw.Draw(img)
for y in range(S):
    t = y / (S - 1)
    r = int(252 - 8 * t)
    g = int(253 - 9 * t)
    b = int(252 - 10 * t)
    d.line((0, y, S, y), fill=(r, g, b, 255))

# Center blue circle. Clean, no outer double ring.
cx = cy = 512
R = 330
circle = Image.new("RGBA", (S, S), (0, 0, 0, 0))
cd = ImageDraw.Draw(circle)
for y in range(cy - R, cy + R + 1):
    for x in range(cx - R, cx + R + 1):
        dx, dy = x - cx, y - cy
        if dx*dx + dy*dy <= R*R:
            t = (dy + R) / (2 * R)
            # Softer cyan-blue, closer to reference.
            rr = int(37 - 10 * t)
            gg = int(184 - 28 * t)
            bb = int(236 - 2 * t)
            circle.putpixel((x, y), (rr, gg, bb, 255))
img.alpha_composite(circle)
d = ImageDraw.Draw(img)

white = (255, 255, 255, 255)
blue_cut = (32, 168, 231, 255)

# Simplified white modem/router glyph, smaller and cleaner than previous version.
# Wi-Fi arcs: two clean arcs plus center dot, closer to the compact reference symbol.
arc_center_y = 438
for r, width, alpha in [(72, 12, 255), (132, 11, 230)]:
    bbox = (cx-r, arc_center_y-r, cx+r, arc_center_y+r)
    d.arc(bbox, start=210, end=330, fill=(255, 255, 255, alpha), width=width)
d.ellipse((cx-14, arc_center_y-14, cx+14, arc_center_y+14), fill=white)

# Modem body: smaller, flatter, and less detailed.
body = (350, 528, 674, 634)
d.rounded_rectangle(body, radius=32, fill=white)
# Front blue cutout, only one simple band.
d.rounded_rectangle((390, 590, 634, 614), radius=11, fill=blue_cut)
# Optical port left.
d.ellipse((392, 552, 440, 600), fill=blue_cut)
d.ellipse((407, 567, 425, 585), fill=white)
# Two tiny LED dots only.
for x in (520, 570):
    d.ellipse((x-10, 566-10, x+10, 566+10), fill=blue_cut)
    d.ellipse((x-4, 566-4, x+4, 566+4), fill=white)

# Two short antennas, simplified and kept inside the blue circle.
d.line((392, 530, 344, 438), fill=white, width=17)
d.line((632, 530, 680, 438), fill=white, width=17)
d.ellipse((336, 430, 352, 446), fill=white)
d.ellipse((672, 430, 688, 446), fill=white)

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

print(PNG1024)
print(ICONSET)
