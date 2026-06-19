#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets"
ICONSET = ASSETS / "AppIcon.iconset"
PNG1024 = ASSETS / "AppIcon-1024.png"

ASSETS.mkdir(parents=True, exist_ok=True)
ICONSET.mkdir(parents=True, exist_ok=True)

S = 1024
cx = cy = S // 2

# Important: the icon canvas itself is an opaque, clean white square.
# No transparent margin, no gray gradient, no rounded card, no shadow.
# This avoids the gray/transparent outer ring seen in Finder previews.
img = Image.new("RGB", (S, S), (255, 255, 255))
d = ImageDraw.Draw(img)

# Large centered blue circle, matching the requested structure:
# white outside + circular blue center.  Radius intentionally increased.
R = 405
for y in range(cy - R, cy + R + 1):
    for x in range(cx - R, cx + R + 1):
        dx, dy = x - cx, y - cy
        if dx * dx + dy * dy <= R * R:
            # Subtle vertical blue gradient only inside the circle.
            t = (dy + R) / (2 * R)
            rr = int(37 - 10 * t)
            gg = int(184 - 28 * t)
            bb = int(236 - 2 * t)
            img.putpixel((x, y), (rr, gg, bb))

d = ImageDraw.Draw(img)
white = (255, 255, 255)
blue_cut = (32, 168, 231)

# White network-device glyph, scaled up to fit the larger blue circle.
# Wi-Fi arcs.
arc_center_y = 405
for r, width in [(82, 15), (150, 14)]:
    bbox = (cx - r, arc_center_y - r, cx + r, arc_center_y + r)
    d.arc(bbox, start=210, end=330, fill=white, width=width)
d.ellipse((cx - 16, arc_center_y - 16, cx + 16, arc_center_y + 16), fill=white)

# Antennas kept fully inside the circle.
d.line((382, 535, 318, 415), fill=white, width=20)
d.line((642, 535, 706, 415), fill=white, width=20)
d.ellipse((308, 405, 328, 425), fill=white)
d.ellipse((696, 405, 716, 425), fill=white)

# Modem body.
body = (318, 528, 706, 660)
d.rounded_rectangle(body, radius=38, fill=white)

# Simple blue details on the modem face.
d.rounded_rectangle((365, 612, 659, 642), radius=14, fill=blue_cut)
d.ellipse((372, 558, 430, 616), fill=blue_cut)
d.ellipse((392, 578, 410, 596), fill=white)
for x in (532, 592):
    d.ellipse((x - 12, 585 - 12, x + 12, 585 + 12), fill=blue_cut)
    d.ellipse((x - 5, 585 - 5, x + 5, 585 + 5), fill=white)

# Save source PNG as opaque RGB. Do not introduce alpha in resized icon assets.
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
