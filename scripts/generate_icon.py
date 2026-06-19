#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets"
ICONSET = ASSETS / "AppIcon.iconset"
PNG1024 = ASSETS / "AppIcon-1024.png"
ICNS = ASSETS / "AppIcon.icns"
RES_ICNS = ROOT / "Resources" / "AppIcon.icns"

ICONSET.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Full-bleed macOS-style background with gradient.
# Keep every pixel opaque so Finder does not show a gray transparent ring.
bg = Image.new("RGBA", (S, S), (0, 0, 0, 255))
bd = ImageDraw.Draw(bg)
for y in range(S):
    t = y / (S - 1)
    r = int(20 + 20 * (1 - t))
    g = int(118 + 70 * (1 - t))
    b = int(230 + 20 * (1 - t))
    bd.line([(0, y), (S, y)], fill=(r, g, b, 255))
img.alpha_composite(bg)
# Add an inner rounded highlight instead of transparent outer padding.
d.rounded_rectangle((42, 42, S-42, S-42), radius=190, outline=(255, 255, 255, 52), width=8)

# Subtle grid/network glow.
glow = Image.new("RGBA", (S, S), (0,0,0,0))
gd = ImageDraw.Draw(glow)
for x in [230, 512, 794]:
    gd.line((x, 190, x, 820), fill=(255,255,255,34), width=4)
for y in [260, 430, 650, 790]:
    gd.line((170, y, 850, y), fill=(255,255,255,28), width=4)
for p in [(230,260),(512,430),(794,650),(512,790)]:
    gd.ellipse((p[0]-16,p[1]-16,p[0]+16,p[1]+16), fill=(145,225,255,80))
img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(1.2)))

# Shadow for modem.
shadow = Image.new("RGBA", (S, S), (0,0,0,0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle((210, 468, 814, 692), radius=64, fill=(0,30,80,120))
shadow = shadow.filter(ImageFilter.GaussianBlur(22))
img.alpha_composite(shadow)

# Modem body.
body = (190, 460, 834, 685)
d.rounded_rectangle(body, radius=62, fill=(246, 250, 255, 255))
d.rounded_rectangle(body, radius=62, outline=(214, 230, 248, 255), width=8)
# Front lower band.
d.rounded_rectangle((214, 595, 810, 665), radius=34, fill=(224, 238, 252, 255))

# Fiber/optical symbol on top-left.
d.ellipse((272, 512, 348, 588), fill=(32, 148, 255, 255))
d.ellipse((294, 534, 326, 566), fill=(217, 246, 255, 255))
for a in range(0, 360, 45):
    cx, cy = 310, 550
    r1, r2 = 58, 78
    x1 = cx + math.cos(math.radians(a))*r1
    y1 = cy + math.sin(math.radians(a))*r1
    x2 = cx + math.cos(math.radians(a))*r2
    y2 = cy + math.sin(math.radians(a))*r2
    d.line((x1,y1,x2,y2), fill=(180,235,255,230), width=7)

# Status LEDs.
leds = [(445, 548, (30, 210, 115,255)), (515, 548, (72, 190, 255,255)), (585, 548, (255, 192, 45,255)), (655, 548, (30,210,115,255))]
for x,y,c in leds:
    d.ellipse((x-18,y-18,x+18,y+18), fill=c)
    d.ellipse((x-28,y-28,x+28,y+28), outline=(255,255,255,180), width=4)

# Ethernet slots.
for x in [430, 515, 600, 685]:
    d.rounded_rectangle((x-26, 618, x+26, 646), radius=8, fill=(80, 125, 170, 255))
    d.rectangle((x-16, 618, x+16, 631), fill=(34, 74, 120, 255))

# Antennas.
for base_x, lean in [(290, -80), (734, 80)]:
    d.line((base_x, 466, base_x + lean, 292), fill=(237, 247, 255, 255), width=28)
    d.line((base_x, 466, base_x + lean, 292), fill=(174, 215, 248, 255), width=8)
    d.ellipse((base_x + lean - 20, 292 - 20, base_x + lean + 20, 292 + 20), fill=(237,247,255,255))

# Wi-Fi arcs.
for r,w,alpha in [(118,12,210),(172,10,150),(226,8,105)]:
    bbox=(512-r,355-r,512+r,355+r)
    d.arc(bbox, start=210, end=330, fill=(220,246,255,alpha), width=w)
d.ellipse((497, 422, 527, 452), fill=(220,246,255,220))

# Tiny text mark.
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 54)
except Exception:
    font = ImageFont.load_default()
d.text((380, 715), "光猫", fill=(225, 245, 255, 230), font=font)

PNG1024.parent.mkdir(exist_ok=True)
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
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(ICONSET / name)

print(PNG1024)
print(ICONSET)
