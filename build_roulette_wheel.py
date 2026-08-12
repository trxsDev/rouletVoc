import os
import math
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1024, 1024
CX, CY = WIDTH // 2, HEIGHT // 2
R_OUTER = 490
R_SECTOR = 435
R_HUB = 105

# Initialize High-Res RGBA Canvas
canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 1. 4 Quadrant Sectors (No text, pure vibrant themed color quadrants)
# Wedge 0 (0° to 90°, Center 45°): จีบนิ้ว (Amber / Orange)
# Wedge 1 (90° to 180°, Center 135°): กำมือ (Crimson Red)
# Wedge 2 (180° to 270°, Center 225°): ชู 2 นิ้ว (Purple)
# Wedge 3 (270° to 360°, Center 315°): แบมือ (Emerald Green)
sectors = [
    {"idx": 0, "file": "gesture_pinch.png", "col1": (245, 158, 11, 255), "deg_start": 0, "deg_end": 90, "deg_mid": 45},
    {"idx": 1, "file": "gesture_fist.png", "col1": (239, 68, 68, 255), "deg_start": 90, "deg_end": 180, "deg_mid": 135},
    {"idx": 2, "file": "gesture_peace.png", "col1": (168, 85, 247, 255), "deg_start": 180, "deg_end": 270, "deg_mid": 225},
    {"idx": 3, "file": "gesture_palm.png", "col1": (16, 185, 129, 255), "deg_start": 270, "deg_end": 360, "deg_mid": 315},
]

# Draw smooth anti-aliased sectors
for s in sectors:
    bbox = [CX - R_SECTOR, CY - R_SECTOR, CX + R_SECTOR, CY + R_SECTOR]
    draw.pieslice(bbox, start=s["deg_start"], end=s["deg_end"], fill=s["col1"], outline=(15, 23, 42, 255), width=2)

# 2. Golden Embossed Divider Spokes
for s in sectors:
    ang_rad = math.radians(s["deg_start"])
    x2 = CX + int(R_SECTOR * math.cos(ang_rad))
    y2 = CY + int(R_SECTOR * math.sin(ang_rad))
    # Golden Spoke Line with dual highlight
    draw.line([(CX, CY), (x2, y2)], fill=(254, 240, 138, 255), width=7)
    draw.line([(CX, CY), (x2, y2)], fill=(180, 83, 9, 255), width=2)

# 3. Paste 4 Pure White Circular Pods with 3D Gestures (No text)
assets_gestures = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets/gestures"
badge_r = 290

for s in sectors:
    rad = math.radians(s["deg_mid"])
    
    pod_x = int(CX + badge_r * math.cos(rad))
    pod_y = int(CY + badge_r * math.sin(rad))
    pod_rad = 88

    # Outer drop shadow for pod
    draw.ellipse([pod_x - pod_rad - 4, pod_y - pod_rad - 4, pod_x + pod_rad + 4, pod_y + pod_rad + 4], fill=(15, 23, 42, 120))
    # Pure Solid White Circular Pod
    draw.ellipse([pod_x - pod_rad, pod_y - pod_rad, pod_x + pod_rad, pod_y + pod_rad], fill=(255, 255, 255, 255), outline=(254, 240, 138, 255), width=4)
    draw.ellipse([pod_x - (pod_rad - 6), pod_y - (pod_rad - 6), pod_x + (pod_rad - 6), pod_y + (pod_rad - 6)], outline=(226, 232, 240, 255), width=2)

    # Paste Gesture Icon with prominent size
    g_path = os.path.join(assets_gestures, s["file"])
    if os.path.exists(g_path):
        g_img = Image.open(g_path).convert("RGBA")
        g_size = (136, 136)
        g_resized = g_img.resize(g_size, Image.Resampling.LANCZOS)
        canvas.paste(g_resized, (pod_x - g_size[0] // 2, pod_y - g_size[1] // 2), g_resized)

# 4. Outer Golden Metallic Rim & LED Bulbs
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

# 5. Center Golden Hub with Diamond Accent
draw.ellipse([CX - R_HUB, CY - R_HUB, CX + R_HUB, CY + R_HUB], fill=(15, 23, 42, 255), outline=(217, 119, 6, 255), width=10)
draw.ellipse([CX - (R_HUB - 8), CY - (R_HUB - 8), CX + (R_HUB - 8), CY + (R_HUB - 8)], fill=(245, 158, 11, 255), outline=(254, 240, 138, 255), width=6)
draw.ellipse([CX - (R_HUB - 35), CY - (R_HUB - 35), CX + (R_HUB - 35), CY + (R_HUB - 35)], fill=(254, 240, 138, 255), outline=(217, 119, 6, 255), width=4)
draw.ellipse([CX - 28, CY - 28, CX + 28, CY + 28], fill=(255, 255, 255, 255))

# Save High-Definition Roulette Wheel
target_path = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets/ui/roulette_wheel.png"
canvas.save(target_path, "PNG")
print("Clean White-Pod Roulette Wheel without text generated successfully at:", target_path)
