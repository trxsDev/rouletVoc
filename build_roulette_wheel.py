import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1024, 1024
CX, CY = WIDTH // 2, HEIGHT // 2
R_OUTER = 490
R_RIM = 440
R_SECTOR = 430
R_HUB = 110

# Initialize High-Res RGBA Canvas
canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 1. 4 Quadrant Sectors
# Wedge 0 (0° to 90°, Center 45°): จีบนิ้ว (Amber/Orange)
# Wedge 1 (90° to 180°, Center 135°): กำมือ (Red)
# Wedge 2 (180° to 270°, Center 225°): ชู 2 นิ้ว (Purple)
# Wedge 3 (270° to 360°, Center 315°): แบมือ (Green)
sectors = [
    {"idx": 0, "name": "จีบนิ้ว", "file": "gesture_pinch.png", "col1": (245, 158, 11, 255), "col2": (217, 119, 6, 255), "deg_start": 0, "deg_end": 90, "deg_mid": 45},
    {"idx": 1, "name": "กำมือ", "file": "gesture_fist.png", "col1": (239, 68, 68, 255), "col2": (185, 28, 28, 255), "deg_start": 90, "deg_end": 180, "deg_mid": 135},
    {"idx": 2, "name": "ชู 2 นิ้ว", "file": "gesture_peace.png", "col1": (168, 85, 247, 255), "col2": (126, 34, 206, 255), "deg_start": 180, "deg_end": 270, "deg_mid": 225},
    {"idx": 3, "name": "แบมือ", "file": "gesture_palm.png", "col1": (16, 185, 129, 255), "col2": (4, 120, 87, 255), "deg_start": 270, "deg_end": 360, "deg_mid": 315},
]

# Draw smooth anti-aliased sectors
for s in sectors:
    # Sector pie slice
    bbox = [CX - R_SECTOR, CY - R_SECTOR, CX + R_SECTOR, CY + R_SECTOR]
    draw.pieslice(bbox, start=s["deg_start"], end=s["deg_end"], fill=s["col1"], outline=(15, 23, 42, 255), width=3)

# 2. Golden Embossed Divider Spokes
for s in sectors:
    ang_rad = math.radians(s["deg_start"])
    x2 = CX + int(R_SECTOR * math.cos(ang_rad))
    y2 = CY + int(R_SECTOR * math.sin(ang_rad))
    # Golden Spoke Line with highlight
    draw.line([(CX, CY), (x2, y2)], fill=(254, 240, 138, 255), width=6)
    draw.line([(CX, CY), (x2, y2)], fill=(217, 119, 6, 255), width=2)

# 3. Paste 4 3D Gesture Badges & Thai Text Labels in each Sector
assets_gestures = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets/gestures"
try:
    font_th = ImageFont.truetype("/System/Library/Fonts/Supplemental/SukhumvitSet.ttc", 36)
except Exception:
    font_th = ImageFont.load_default()

badge_r = 275
text_r = 380

for s in sectors:
    rad = math.radians(s["deg_mid"])
    
    # 1. Circular Badge Pod Background
    pod_x = int(CX + badge_r * math.cos(rad))
    pod_y = int(CY + badge_r * math.sin(rad))
    pod_rad = 75
    draw.ellipse([pod_x - pod_rad, pod_y - pod_rad, pod_x + pod_rad, pod_y + pod_rad], fill=(15, 23, 42, 230), outline=(254, 240, 138, 255), width=4)

    # 2. Paste Gesture Icon
    g_path = os.path.join(assets_gestures, s["file"])
    if os.path.exists(g_path):
        g_img = Image.open(g_path).convert("RGBA")
        g_size = (120, 120)
        g_resized = g_img.resize(g_size, Image.Resampling.LANCZOS)
        canvas.paste(g_resized, (pod_x - g_size[0] // 2, pod_y - g_size[1] // 2), g_resized)

    # 3. Draw Thai Text Badge
    tx = int(CX + text_r * math.cos(rad))
    ty = int(CY + text_r * math.sin(rad))
    t_bbox = font_th.getbbox(s["name"])
    tw, th = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
    
    # Pill background for text
    pill_pad_x, pill_pad_y = 18, 8
    pill_rect = [tx - tw // 2 - pill_pad_x, ty - th // 2 - pill_pad_y, tx + tw // 2 + pill_pad_x, ty + th // 2 + pill_pad_y]
    draw.rounded_rectangle(pill_rect, radius=12, fill=(15, 23, 42, 240), outline=(254, 240, 138, 255), width=2)
    draw.text((tx - tw // 2, ty - th // 2 - 4), s["name"], font=font_th, fill=(255, 255, 255, 255))

# 4. Outer Golden Metallic Rim & LED Bulbs
# Outer ring glow
draw.ellipse([CX - R_OUTER, CY - R_OUTER, CX + R_OUTER, CY + R_OUTER], outline=(217, 119, 6, 255), width=32)
draw.ellipse([CX - (R_OUTER - 8), CY - (R_OUTER - 8), CX + (R_OUTER - 8), CY + (R_OUTER - 8)], outline=(254, 240, 138, 255), width=8)
draw.ellipse([CX - (R_OUTER - 16), CY - (R_OUTER - 16), CX + (R_OUTER - 16), CY + (R_OUTER - 16)], outline=(180, 83, 9, 255), width=6)
draw.ellipse([CX - R_SECTOR, CY - R_SECTOR, CX + R_SECTOR, CY + R_SECTOR], outline=(15, 23, 42, 255), width=5)

# 16 Glowing LED Bulbs on the rim
num_leds = 16
for i in range(num_leds):
    led_ang = math.radians(i * (360.0 / num_leds))
    lx = int(CX + (R_OUTER - 14) * math.cos(led_ang))
    ly = int(CY + (R_OUTER - 14) * math.sin(led_ang))
    # Glowing bulb
    draw.ellipse([lx - 12, ly - 12, lx + 12, ly + 12], fill=(254, 240, 138, 255), outline=(245, 158, 11, 255), width=2)
    draw.ellipse([lx - 6, ly - 6, lx + 6, ly + 6], fill=(255, 255, 255, 255))

# 5. Center Golden Hub
draw.ellipse([CX - R_HUB, CY - R_HUB, CX + R_HUB, CY + R_HUB], fill=(15, 23, 42, 255), outline=(217, 119, 6, 255), width=10)
draw.ellipse([CX - (R_HUB - 8), CY - (R_HUB - 8), CX + (R_HUB - 8), CY + (R_HUB - 8)], fill=(245, 158, 11, 255), outline=(254, 240, 138, 255), width=6)
draw.ellipse([CX - (R_HUB - 35), CY - (R_HUB - 35), CX + (R_HUB - 35), CY + (R_HUB - 35)], fill=(254, 240, 138, 255), outline=(217, 119, 6, 255), width=4)
draw.ellipse([CX - 28, CY - 28, CX + 28, CY + 28], fill=(255, 255, 255, 255))

# Save High-Definition Roulette Wheel
target_path = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets/ui/roulette_wheel.png"
canvas.save(target_path, "PNG")
print("High-definition, mathematically aligned Roulette Wheel generated successfully at:", target_path)
