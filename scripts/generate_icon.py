#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets"
ICONSET = ASSETS / "AppIcon.iconset"
PNG1024 = ASSETS / "AppIcon-1024.png"

ASSETS.mkdir(parents=True, exist_ok=True)
ICONSET.mkdir(parents=True, exist_ok=True)

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Reference-style composition:
# soft shadow + light rounded square tile + centered blue circle + white simple modem/fiber glyph.
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle((92, 104, 932, 944), radius=205, fill=(0, 0, 0, 62))
shadow = shadow.filter(ImageFilter.GaussianBlur(30))
img.alpha_composite(shadow)

tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
td = ImageDraw.Draw(tile)
# Subtle warm-gray vertical gradient, like the provided reference.
for y in range(S):
    t = y / (S - 1)
    v = int(248 - 10 * t)
    td.line((0, y, S, y), fill=(v, v, v - 2, 255))
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle((88, 88, 936, 936), radius=205, fill=255)
img.alpha_composite(Image.composite(tile, Image.new("RGBA", (S, S), (0,0,0,0)), mask))

# Very light inner highlight/border on tile.
d = ImageDraw.Draw(img)
d.rounded_rectangle((94, 94, 930, 930), radius=198, outline=(255, 255, 255, 135), width=6)
d.rounded_rectangle((88, 88, 936, 936), radius=205, outline=(218, 224, 230, 95), width=3)

# Center blue circle, flat and clean.
cx = cy = 512
R = 306
# Slight gradient in the blue circle, but keep it simple.
circle = Image.new("RGBA", (S, S), (0,0,0,0))
cd = ImageDraw.Draw(circle)
for yy in range(cy - R, cy + R + 1):
    for xx in range(cx - R, cx + R + 1):
        dx, dy = xx - cx, yy - cy
        if dx*dx + dy*dy <= R*R:
            t = (dy + R) / (2*R)
            r = int(37 - 10*t)
            g = int(178 - 34*t)
            b = int(238 - 4*t)
            circle.putpixel((xx, yy), (r, g, b, 255))
img.alpha_composite(circle)
# Subtle circle highlight.
d = ImageDraw.Draw(img)
d.ellipse((cx-R+8, cy-R+8, cx+R-8, cy+R-8), outline=(255,255,255,38), width=7)

# White optical modem glyph inside circle.
# Main modem body: simple rounded rectangle.
white = (255, 255, 255, 255)
soft = (232, 248, 255, 245)
body = (346, 508, 678, 626)
d.rounded_rectangle(body, radius=38, fill=white)
# Front band cut via blue overlay to mimic a clean flat symbol.
d.rounded_rectangle((378, 574, 646, 602), radius=14, fill=(35, 160, 225, 255))
# Optical/fiber port circle.
d.ellipse((386, 534, 438, 586), fill=(35, 160, 225, 255))
d.ellipse((402, 550, 422, 570), fill=white)
# LED dots.
for x in (492, 540, 588):
    d.ellipse((x-12, 546-12, x+12, 546+12), fill=(35, 160, 225, 255))
    d.ellipse((x-5, 546-5, x+5, 546+5), fill=white)

# Optical fiber/wifi-like arcs above, compact and symmetric.
for r, width, alpha in [(78, 16, 255), (128, 14, 235), (180, 12, 210)]:
    bbox = (cx-r, 430-r, cx+r, 430+r)
    d.arc(bbox, start=205, end=335, fill=(255,255,255,alpha), width=width)
d.ellipse((cx-18, 430-18, cx+18, 430+18), fill=white)

# Two small antenna strokes, simplified.
d.line((396, 511, 344, 406), fill=soft, width=22)
d.line((628, 511, 680, 406), fill=soft, width=22)
d.ellipse((334, 396, 354, 416), fill=soft)
d.ellipse((670, 396, 690, 416), fill=soft)

# Small optical sparkle/fiber node in the upper-right, still no text.
for a in range(0, 360, 60):
    x1 = 648 + math.cos(math.radians(a))*25
    y1 = 384 + math.sin(math.radians(a))*25
    x2 = 648 + math.cos(math.radians(a))*43
    y2 = 384 + math.sin(math.radians(a))*43
    d.line((x1,y1,x2,y2), fill=(255,255,255,210), width=8)
d.ellipse((628, 364, 668, 404), fill=white)
d.ellipse((640, 376, 656, 392), fill=(35,160,225,255))

# Export source png and iconset.
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
