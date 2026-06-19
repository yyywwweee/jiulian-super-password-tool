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
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Soft shadow, similar to the reference app-icon tile.
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle((38, 50, 986, 1002), radius=210, fill=(0, 0, 0, 48))
shadow = shadow.filter(ImageFilter.GaussianBlur(24))
img.alpha_composite(shadow)

# Large white rounded-square outer tile, close to canvas edge.
tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
td = ImageDraw.Draw(tile)
for y in range(S):
    t = y / (S - 1)
    r = int(250 - 12 * t)
    g = int(251 - 13 * t)
    b = int(250 - 14 * t)
    td.line((0, y, S, y), fill=(r, g, b, 255))
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
# Smaller transparent margin than previous version.
md.rounded_rectangle((34, 34, 990, 990), radius=218, fill=255)
img.alpha_composite(Image.composite(tile, Image.new("RGBA", (S, S), (0,0,0,0)), mask))

d = ImageDraw.Draw(img)
# Very subtle edge; avoid obvious gray ring.
d.rounded_rectangle((38, 38, 986, 986), radius=214, outline=(224, 229, 232, 42), width=2)

# Center blue circle. Clean, no outer double ring.
cx = cy = 512
R = 260
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
arc_center_y = 452
for r, width, alpha in [(58, 10, 255), (106, 9, 230)]:
    bbox = (cx-r, arc_center_y-r, cx+r, arc_center_y+r)
    d.arc(bbox, start=210, end=330, fill=(255, 255, 255, alpha), width=width)
d.ellipse((cx-11, arc_center_y-11, cx+11, arc_center_y+11), fill=white)

# Modem body: smaller, flatter, and less detailed.
body = (386, 532, 638, 612)
d.rounded_rectangle(body, radius=25, fill=white)
# Front blue cutout, only one simple band.
d.rounded_rectangle((420, 576, 604, 594), radius=9, fill=blue_cut)
# Optical port left.
d.ellipse((420, 548, 452, 580), fill=blue_cut)
d.ellipse((431, 559, 441, 569), fill=white)
# Two tiny LED dots only.
for x in (520, 560):
    d.ellipse((x-7, 558-7, x+7, 558+7), fill=blue_cut)
    d.ellipse((x-3, 558-3, x+3, 558+3), fill=white)

# Two short antennas, simplified and kept inside the blue circle.
d.line((422, 534, 388, 468), fill=white, width=13)
d.line((602, 534, 636, 468), fill=white, width=13)
d.ellipse((382, 462, 394, 474), fill=white)
d.ellipse((630, 462, 642, 474), fill=white)

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
