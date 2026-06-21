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
import struct
import io
subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)], check=True)

# === Windows .ico ===
# 从头超采样绘制每个尺寸（8x），再手写 .ico 打包
ico_sizes = [(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(128,128),(256,256)]
images = {}
for w, h in ico_sizes:
    # 8x supersampling
    SS2 = 8
    W2, cx2, cy2 = w * SS2, w * SS2 // 2, h * SS2 // 2
    img2 = Image.new("RGBA", (W2, W2), (0,0,0,0))
    d2 = ImageDraw.Draw(img2)
    corner2 = int(W2 * 0.225)
    d2.rounded_rectangle((0, 0, W2-1, W2-1), radius=corner2, fill=(255,255,255,255))
    R2 = int(W2 * 0.395)
    for yy in range(cy2 - R2, cy2 + R2 + 1):
        for xx in range(cx2 - R2, cx2 + R2 + 1):
            dx2, dy2 = xx - cx2, yy - cy2
            if dx2*dx2 + dy2*dy2 <= R2*R2:
                t2 = (dy2 + R2) / (2*R2)
                img2.putpixel((xx, yy), (int(37-10*t2), int(184-28*t2), int(236-2*t2), 255))
    d2 = ImageDraw.Draw(img2)
    white2, blue2 = (255,255,255,255), (32,168,231,255)
    for rr2_pct, ww2_pct in [(0.160, 0.014), (0.293, 0.012)]:
        rr2, ww2 = int(rr2_pct*W2), max(1, int(ww2_pct*W2))
        bbox2 = (cx2-rr2, int(W2*0.395)-rr2, cx2+rr2, int(W2*0.395)+rr2)
        d2.arc(bbox2, 210, 330, fill=white2, width=ww2)
    dr2 = max(1, int(W2*0.0156))
    d2.ellipse((cx2-dr2, int(W2*0.395)-dr2, cx2+dr2, int(W2*0.395)+dr2), fill=white2)
    lw2 = max(2, int(W2*0.0195))
    d2.line((int(W2*0.373), int(W2*0.522), int(W2*0.311), int(W2*0.405)), fill=white2, width=lw2)
    d2.line((int(W2*0.627), int(W2*0.522), int(W2*0.689), int(W2*0.405)), fill=white2, width=lw2)
    dr2 = max(2, int(W2*0.01))
    d2.ellipse((int(W2*0.301), int(W2*0.395), int(W2*0.321), int(W2*0.415)), fill=white2)
    d2.ellipse((int(W2*0.680), int(W2*0.395), int(W2*0.700), int(W2*0.415)), fill=white2)
    d2.rounded_rectangle((int(W2*0.311), int(W2*0.516), int(W2*0.689), int(W2*0.645)), radius=max(3, int(W2*0.037)), fill=white2)
    d2.rounded_rectangle((int(W2*0.357), int(W2*0.598), int(W2*0.644), int(W2*0.627)), radius=max(2, int(W2*0.014)), fill=blue2)
    d2.ellipse((int(W2*0.363), int(W2*0.545), int(W2*0.420), int(W2*0.602)), fill=blue2)
    d2.ellipse((int(W2*0.383), int(W2*0.565), int(W2*0.400), int(W2*0.582)), fill=white2)
    for px2 in [int(W2*0.520), int(W2*0.578)]:
        d2.ellipse((px2-int(W2*0.012), int(W2*0.571)-int(W2*0.012), px2+int(W2*0.012), int(W2*0.571)+int(W2*0.012)), fill=blue2)
        d2.ellipse((px2-int(W2*0.005), int(W2*0.571)-int(W2*0.005), px2+int(W2*0.005), int(W2*0.571)+int(W2*0.005)), fill=white2)
    images[(w,h)] = img2.resize((w, h), Image.Resampling.LANCZOS)

# 手写 ICO（每个尺寸独立 PNG 数据）
entries, png_data, offset = [], [], 6 + 16 * len(ico_sizes)
for (w, h), im in sorted(images.items(), key=lambda x: x[0][0]*x[0][1], reverse=True):
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    png_data.append(png_bytes)
    ew = 0 if w >= 256 else w
    eh = 0 if h >= 256 else h
    entries.append(struct.pack('<BBBBHHII', ew, eh, 0, 0, 1, 32, len(png_bytes), offset))
    offset += len(png_bytes)
with open(ICO, 'wb') as f:
    f.write(struct.pack('<HHH', 0, 1, len(entries)))
    for e in entries: f.write(e)
    for d in png_data: f.write(d)

print(PNG1024)
print(ICONSET)
print(ICNS)
print(ICO)
